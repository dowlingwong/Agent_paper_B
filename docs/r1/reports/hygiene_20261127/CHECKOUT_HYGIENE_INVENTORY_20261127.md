# Checkout hygiene inventory (local/20261126-13; tier D; nothing removed, nothing stashed)

AI-assisted (Claude, Mac-desk worker), 27 Nov 2026. Read-only, from the Mac checkout (`~/agent_paper_B`) and its worktree
list (origin/main `47df6f55`). Runbook §2 order 0; `docs/r1/reports/REPO_HYGIENE_AUDIT_20261126.md`; canon rule 2. The author decides.

## Summary

- **Retire: 72.** Each is clean, and its tip is merged into `main` or held by a remote ref; the row gives the recovery ref and tip.
- **Keep: 14.** Uncommitted edits, or a tip on no remote ref.
- **In active use: 6.** Worker sessions and live agents.
- **Not listed:** session scratch trees in the system temp directory. Their paths are left out of this published record.

**How to retire one:** `git worktree remove <path>` (only when clean), then `git worktree prune`. The branch and its remote ref stay.

**A worktree marked "keep: uncommitted edits"** is cleared by its owner first.

**Untracked directories at the checkout root (54):** `.iso_h200_work/`, `.tmp_ar_g1b_monitor/`, `.tmp_ar_pin_inspect/`, `.tmp_ar_pin_work/`, `.tmp_etth1_20261125/`, `.tmp_etth1_u2_20261125/`, `.tmp_forestcover_20261125/`, `.tmp_forestcover_u2_20261125/`, `.tmp_g1b_fmnist_20261122/`, `.tmp_g5prep/`, `.tmp_hostcheck_g0/`, `.tmp_metamaze_20261125/`, `.tmp_metamaze_u2_20261125/`, `.tmp_plan_ff_20261123/`, `.tmp_smeas_result_20261123/`, `.tmp_tasl2_ar_pin_r2/`, `.tmp_tasl2_cpu_stability_20261125/`, `.tmp_tasl2_hostcheck/`, `.tmp_tasl2_t1_prep/`, `.tmp_tasl7_cpu_stability_20261126/`, `.tmp_tasl7_hostcheck/`, `.tmp_titanic_u2_20261125/`, `.tmp_v21_diag/`, `.tmp_v21_review/`, `.u2_iso_20261119_patch.py`, `.u2_iso_20261119_patch2.py`, `.u2_iso_20261119_patch3.py`, `.u2_iso_derive_mid.py`, `.u2_iso_gen_report.py`, `.u2_iso_tmp/`, `archive/local-20261126/`, `docs/r1/reports/tasl_chain_20261122/METAMAZE_U2_RESULT_20261125_RETRY.md`, `docs/r1/reports/tasl_chain_20261122/captures/MANIFEST.sha256`, `docs/r1/reports/tasl_chain_20261122/captures/dates_recompute.err`, `docs/r1/reports/tasl_chain_20261122/captures/dates_recompute.json`, `docs/r1/reports/tasl_chain_20261122/captures/metamaze_u2_retry_20261125/`, `docs/r1/reports/tasl_chain_20261122/captures/mlab_cifar10/`, `docs/r1/reports/tasl_chain_20261122/captures/mlgym_breakout_minatar/`, `docs/r1/reports/tasl_chain_20261122/captures/mlgym_fmnist/`, `docs/r1/reports/tasl_chain_20261122/captures/pilot_totals.json`, `docs/r1/reports/tasl_chain_20261122/captures/preflight_TASL-2.json`, `docs/r1/reports/tasl_chain_20261122/captures/preflight_TASL-7.json`, `docs/r1/reports/tasl_chain_20261122/captures/server/`, `docs/r1/reports/tasl_chain_20261122/captures/titanic_u2_retry_20261125/`, `docs/r1/reviews/E1_OPENML_REVIEW_20261116.md`, `docs/r1/reviews/E1_REPLAY_REVIEW_20261116.md`, `docs/r1/reviews/EXPB_Q1Q3_RERUN_REVIEW_20261122.md`, `docs/r1/reviews/P4_HOST_CONFIG_FILL_FRESH_REVIEW_20261126.md`, `docs/r1/reviews/P4_HOST_CONFIG_FILL_REVIEW_20261126.md`, `results/r1/pilot/E1_CLIMATE_DT_20261025_ATTEMPT02/`, `tools/coordinator_status.py`, `tools/prepare_overleaf.py`, `tools/start_workers.py`, `tools/sync-docs-to-mini/`. These are earlier host and census scratch. This inventory did not open them. Proposal: the author moves them to `_to_delete/` once no record on `main` cites them.

## Uncommitted edits in the main checkout (the author's local edits, per STATE.md)

```
 README.md                                          | 34 ++++++++++
 canon/README.md                                    | 18 +++---
 canon/agents/coordinator/SOUL.md                   |  9 ++-
 canon/agents/writer/SOUL.md                        |  3 +-
 .../runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md  | 74 ++++++++++++++++------
 5 files changed, 110 insertions(+), 28 deletions(-)
```

Proposal: commit them through the coordinator, or keep them. Nothing was touched.

## Worktrees

| # | path | branch | tip | merged into main | held by a remote ref | dirty files | proposal |
|---|---|---|---|---|---|---|---|
| 1 | `~/agent_paper_B` | `main` | `ef06a65c` | yes | `origin/HEAD`, `->` | 59 | keep (main checkout) |
| 16 | `~/agent_paper_B-workers/compute` | `coord/compute` | `a7346712` | no | `origin/coord/compute` | 0 | keep: in active use (worker session or live agent) |
| 17 | `~/agent_paper_B-workers/local` | `mac-test-only-20261127` | `ab0b3dd9` | no | `origin/mac-test-only-20261127` | 0 | keep: in active use (worker session or live agent) |
| 18 | `~/agent_paper_B-workers/writer` | `writer-20261126-03-claim-table-sheet` | `acf7d37b` | no | `origin/writer-20261126-03-claim-table-sheet` | 0 | keep: in active use (worker session or live agent) |
| 19 | `~/agent_paper_B/.claude-worktrees/b1-d-report-20261114` | `b1-d-report-20261114` | `fcf52c09` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ fcf52c09 |
| 20 | `~/agent_paper_B/.claude-worktrees/b1-diag-20261109` | `(detached)` | `7b08c2ad` | no | no | 0 | keep: tip on no remote ref |
| 21 | `~/agent_paper_B/.claude-worktrees/b1-status-20261115` | `mac-b1-20261107` | `78afa073` | yes | `origin/mac-b1-20261107` | 0 | retire; recovery: main @ 78afa073 |
| 22 | `~/agent_paper_B/.claude-worktrees/b2-ops-fix-20261115` | `(detached)` | `55fd2652` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ 55fd2652 |
| 23 | `~/agent_paper_B/.claude-worktrees/b2-postrun-review-20261115` | `(detached)` | `5c3ff87a` | yes | `origin/HEAD`, `->` | 3 | keep: uncommitted edits |
| 24 | `~/agent_paper_B/.claude-worktrees/cluster-resource-card-20261126` | `cluster-resource-card-20261126` | `020c6665` | yes | `origin/cluster-resource-card-20261126` | 0 | retire; recovery: main @ 020c6665 |
| 25 | `~/agent_paper_B/.claude-worktrees/docs-c3b-wdbc-fix-20261121` | `docs-c3b-wdbc-fix-20261121` | `7219a57a` | yes | `origin/docs-c3b-wdbc-fix-20261121` | 0 | retire; recovery: main @ 7219a57a |
| 26 | `~/agent_paper_B/.claude-worktrees/e1-amend-run-review-20261117` | `(detached)` | `7f1e09aa` | yes | `origin/HEAD`, `->` | 1 | keep: uncommitted edits |
| 27 | `~/agent_paper_B/.claude-worktrees/e1-openml-20261116` | `e1-openml-20261116` | `5d73550a` | no | `origin/e1-openml-20261116` | 0 | retire; recovery: origin/e1-openml-20261116 @ 5d73550a |
| 28 | `~/agent_paper_B/.claude-worktrees/e1-openml-amend-20261117` | `r1-e1-openml-amend-20261117` | `bbcfc4a9` | no | `origin/r1-e1-openml-amend-20261117` | 0 | retire; recovery: origin/r1-e1-openml-amend-20261117 @ bbcfc4a9 |
| 29 | `~/agent_paper_B/.claude-worktrees/e1-review-20261116` | `e1-review-20261116` | `fc7d8e4e` | no | `origin/ops-e1-replay-20261116` | 0 | retire; recovery: origin/ops-e1-replay-20261116 @ fc7d8e4e |
| 30 | `~/agent_paper_B/.claude-worktrees/e1-run-report-20261117` | `e1-run-report-20261117` | `52992b22` | yes | `origin/ops-e1-replay-amend-20261117` | 0 | retire; recovery: main @ 52992b22 |
| 31 | `~/agent_paper_B/.claude-worktrees/fix-plan-freeze-20261122` | `fix-plan-freeze-20261122` | `f93264fc` | yes | `origin/fix-plan-freeze-20261122` | 0 | retire; recovery: main @ f93264fc |
| 32 | `~/agent_paper_B/.claude-worktrees/g1b-noise-20261116` | `g1b-noise-20261116` | `231b6693` | no | `origin/g1b-noise-20261116` | 0 | retire; recovery: origin/g1b-noise-20261116 @ 231b6693 |
| 33 | `~/agent_paper_B/.claude-worktrees/hk2-ops-20261109` | `hk2-ops-20261109` | `5021eba7` | no | no | 0 | keep: tip on no remote ref |
| 34 | `~/agent_paper_B/.claude-worktrees/htc-image-v2-20261115` | `htc-image-v2-20261115` | `cbd0238e` | no | `origin/htc-image-v2-20261115` | 21 | keep: uncommitted edits |
| 35 | `~/agent_paper_B/.claude-worktrees/htc-image-v2.2-20261124` | `htc-image-v2.2-20261124` | `667bb9c2` | yes | `origin/htc-image-v2.2-20261124` | 0 | retire; recovery: main @ 667bb9c2 |
| 36 | `~/agent_paper_B/.claude-worktrees/htcondor-chain-20261114` | `htcondor-chain-20261114` | `13050d14` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ 13050d14 |
| 37 | `~/agent_paper_B/.claude-worktrees/htcondor-container-20261115` | `htcondor-container-20261115` | `43e53c81` | no | `origin/htcondor-container-20261115` | 0 | retire; recovery: origin/htcondor-container-20261115 @ 43e53c81 |
| 38 | `~/agent_paper_B/.claude-worktrees/htcondor-prep-20261114` | `htcondor-prep-20261114` | `36cc113c` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ 36cc113c |
| 39 | `~/agent_paper_B/.claude-worktrees/i2-disk-20261123` | `i2-disk-20261123` | `10ae0a23` | yes | `origin/i2-disk-20261123` | 0 | retire; recovery: main @ 10ae0a23 |
| 40 | `~/agent_paper_B/.claude-worktrees/i2-mem-smoke-20261123` | `i2-mem-smoke-20261123` | `e4678334` | yes | `origin/i2-mem-smoke-20261123` | 0 | retire; recovery: main @ e4678334 |
| 41 | `~/agent_paper_B/.claude-worktrees/i2-memory-diag-20261123` | `i2-memory-diag-20261123` | `0dba5dd6` | yes | `origin/i2-memory-diag-20261123` | 0 | retire; recovery: main @ 0dba5dd6 |
| 42 | `~/agent_paper_B/.claude-worktrees/i3-h200-20261119` | `i3-h200-20261119` | `fa838c27` | no | `origin/i3-h200-20261119` | 0 | retire; recovery: origin/i3-h200-20261119 @ fa838c27 |
| 43 | `~/agent_paper_B/.claude-worktrees/local-20261026` | `local-20261026` | `7c8449b0` | yes | `origin/HEAD`, `->` | 1 | keep: uncommitted edits |
| 44 | `~/agent_paper_B/.claude-worktrees/mac-d3-design-20261126` | `mac-d3-design-20261126` | `4f4634c4` | yes | `origin/mac-d3-design-20261126` | 0 | retire; recovery: main @ 4f4634c4 |
| 45 | `~/agent_paper_B/.claude-worktrees/mac-int-20261104` | `mac-int-20261104` | `2f53fcfa` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ 2f53fcfa |
| 46 | `~/agent_paper_B/.claude-worktrees/main-merge` | `(detached)` | `bc31e15e` | yes | `origin/HEAD`, `->` | 482 | keep: uncommitted edits |
| 47 | `~/agent_paper_B/.claude-worktrees/main_t1_ar_binding_20261122` | `main-t1-ar-pin-binding-20261122` | `ebb86248` | yes | `origin/main-t1-ar-pin-binding-20261122` | 0 | retire; recovery: main @ ebb86248 |
| 48 | `~/agent_paper_B/.claude-worktrees/main_t1_g1b_seven_assembly_20261125` | `main-t1-g1b-seven-assembly-20261125` | `01523e03` | yes | `origin/main-t1-g1b-seven-assembly-20261125` | 0 | retire; recovery: main @ 01523e03 |
| 49 | `~/agent_paper_B/.claude-worktrees/main_t1_g4b_pilot_20261125` | `main-t1-g4b-pilot-20261125` | `7115e530` | yes | `origin/main-t1-g4b-pilot-20261125` | 0 | retire; recovery: main @ 7115e530 |
| 50 | `~/agent_paper_B/.claude-worktrees/main_t1_g5_smoke_20261124` | `main-t1-g5-smoke-20261124` | `d8381924` | yes | `origin/main-t1-g5-smoke-20261124` | 0 | retire; recovery: main @ d8381924 |
| 51 | `~/agent_paper_B/.claude-worktrees/main_t1_host_reports_20261121` | `main-t1-host-reports-20261121` | `f86980eb` | yes | `origin/main-t1-host-reports-20261121` | 1 | keep: uncommitted edits |
| 52 | `~/agent_paper_B/.claude-worktrees/main_t1_node_expansion_20261125` | `main-t1-node-expansion-20261125` | `11a8ed47` | yes | `origin/main-t1-node-expansion-20261125` | 0 | retire; recovery: main @ 11a8ed47 |
| 53 | `~/agent_paper_B/.claude-worktrees/main_t1_tasl2_cpu_stability_20261126` | `main-t1-tasl2-cpu-stability-20261126` | `dcf7e8b9` | yes | `origin/main-t1-tasl2-cpu-stability-20261126` | 0 | retire; recovery: main @ dcf7e8b9 |
| 54 | `~/agent_paper_B/.claude-worktrees/main_t1_tasl7_cpu_stability_20261126` | `main-t1-tasl7-cpu-stability-20261126` | `b84a2c80` | yes | `origin/main-t1-tasl7-cpu-stability-20261126` | 0 | retire; recovery: main @ b84a2c80 |
| 55 | `~/agent_paper_B/.claude-worktrees/main_t1_tasl_results_20261125` | `main-t1-tasl-results-20261125` | `d73505bd` | yes | `origin/main-t1-tasl-results-20261125` | 0 | retire; recovery: main @ d73505bd |
| 56 | `~/agent_paper_B/.claude-worktrees/main_t1_xc2_preassembly_20261125` | `main-t1-xc2-preassembly-20261125` | `ab4028ca` | no | `origin/main-t1-xc2-preassembly-20261125` | 0 | retire; recovery: origin/main-t1-xc2-preassembly-20261125 @ ab4028ca |
| 57 | `~/agent_paper_B/.claude-worktrees/main_t1_xc2_verdicts_20261122` | `main-t1-xc2-verdicts-20261122` | `8c326a06` | yes | `origin/main-t1-xc2-verdicts-20261122` | 0 | retire; recovery: main @ 8c326a06 |
| 58 | `~/agent_paper_B/.claude-worktrees/ops-arms-a3-20261123` | `ops-arms-a3-20261123` | `340d288c` | yes | `origin/ops-arms-a3-20261123` | 0 | retire; recovery: main @ 340d288c |
| 59 | `~/agent_paper_B/.claude-worktrees/ops-b1-20261109` | `ops-b1-20261109` | `d1d30687` | no | no | 0 | keep: tip on no remote ref |
| 60 | `~/agent_paper_B/.claude-worktrees/ops-b2-20261115` | `ops-b2-exec-20261115` | `d301ef2f` | yes | `origin/ops-b2-exec-20261115` | 0 | retire; recovery: main @ d301ef2f |
| 61 | `~/agent_paper_B/.claude-worktrees/ops-b2-audit-20261119` | `tmp-b2-review-20261119` | `b41af8e9` | yes | `origin/ops-b2-audit-20261119` | 0 | retire; recovery: main @ b41af8e9 |
| 62 | `~/agent_paper_B/.claude-worktrees/ops-g1b-expansion-hostcheck-20261126` | `main-t1-expansion-hostcheck-20261126` | `2cc9b4fc` | yes | `origin/main-t1-expansion-hostcheck-20261126` | 0 | retire; recovery: main @ 2cc9b4fc |
| 63 | `~/agent_paper_B/.claude-worktrees/ops-g5-prep-20261126` | `main-t1-g5-prep-20261126` | `17d8ca47` | yes | `origin/main-t1-g5-prep-20261126` | 0 | retire; recovery: main @ 17d8ca47 |
| 64 | `~/agent_paper_B/.claude-worktrees/ops-s2-audit-20261122` | `ops-s2-audit-20261122` | `4a5f9690` | yes | `origin/ops-s2-audit-20261122` | 0 | retire; recovery: main @ 4a5f9690 |
| 65 | `~/agent_paper_B/.claude-worktrees/ops-s2-audit-stop-20261122` | `ops-s2-audit-stop-20261122` | `28290172` | no | `origin/ops-s2-audit-stop-20261122` | 0 | retire; recovery: origin/ops-s2-audit-stop-20261122 @ 28290172 |
| 66 | `~/agent_paper_B/.claude-worktrees/ops-s2c3b-launch-stop-20261120` | `ops-s2c3b-launch-stop-20261120` | `0e635c9f` | no | `origin/ops-s2c3b-launch-stop-20261120` | 0 | retire; recovery: origin/ops-s2c3b-launch-stop-20261120 @ 0e635c9f |
| 67 | `~/agent_paper_B/.claude-worktrees/ops-sweep2-launch-20261121` | `ops-sweep2-launch-20261121` | `c9b5e570` | no | `origin/ops-sweep2-launch-20261121` | 0 | retire; recovery: origin/ops-sweep2-launch-20261121 @ c9b5e570 |
| 68 | `~/agent_paper_B/.claude-worktrees/ops-sweep2-report-20261121` | `ops-sweep2-report-20261121` | `e47f3f33` | yes | `origin/ops-sweep2-report-20261121` | 0 | retire; recovery: main @ e47f3f33 |
| 69 | `~/agent_paper_B/.claude-worktrees/ops-sweep2-rte-diag-20261121` | `ops-sweep2-rte-diag-20261121` | `cab74ccd` | yes | `origin/ops-sweep2-rte-diag-20261121` | 0 | retire; recovery: main @ cab74ccd |
| 70 | `~/agent_paper_B/.claude-worktrees/ops-t1-h200-isolation-20261121` | `ops-t1-h200-isolation-20261121` | `9c93d041` | no | `origin/ops-t1-h200-isolation-20261121` | 0 | retire; recovery: origin/ops-t1-h200-isolation-20261121 @ 9c93d041 |
| 71 | `~/agent_paper_B/.claude-worktrees/ops-tasl-20261116` | `ops-tasl-20261116` | `9253192f` | no | `origin/ops-tasl-20261116` | 65 | keep: uncommitted edits |
| 72 | `~/agent_paper_B/.claude-worktrees/ops-tasl-20261116/.claude-worktrees/ops_t1_ar_pin_20261122` | `ops-t1-ar-pin-20261122` | `9090650b` | no | `origin/ops-t1-ar-pin-20261122` | 0 | retire; recovery: origin/ops-t1-ar-pin-20261122 @ 9090650b |
| 73 | `~/agent_paper_B/.claude-worktrees/ops-tasl-20261116/.claude-worktrees/ops_t1_data_manifest_20261122` | `ops-t1-data-manifest-20261122` | `ac298f25` | no | `origin/ops-t1-data-manifest-20261122` | 0 | retire; recovery: origin/ops-t1-data-manifest-20261122 @ ac298f25 |
| 74 | `~/agent_paper_B/.claude-worktrees/p4-hostconfig-fill-20261126` | `p4-hostconfig-fill-20261126` | `021c4eec` | no | `origin/p4-hostconfig-fill-20261126` | 0 | retire; recovery: origin/p4-hostconfig-fill-20261126 @ 021c4eec |
| 75 | `~/agent_paper_B/.claude-worktrees/p4-staging-20261125` | `p4-staging-20261125` | `3bbf2f52` | no | `origin/p4-staging-20261125` | 0 | retire; recovery: origin/p4-staging-20261125 @ 3bbf2f52 |
| 76 | `~/agent_paper_B/.claude-worktrees/rel-sweep1-compat-20261122` | `rel-sweep1-compat-20261122` | `0aaa1716` | yes | `origin/rel-sweep1-compat-20261122` | 0 | retire; recovery: main @ 0aaa1716 |
| 77 | `~/agent_paper_B/.claude-worktrees/release-sweep1-20261123` | `release-sweep1-20261123` | `fbbf981d` | yes | `origin/release-sweep1-20261123` | 0 | retire; recovery: main @ fbbf981d |
| 78 | `~/agent_paper_B/.claude-worktrees/release-traindev-20261122` | `release-traindev-20261122` | `72373e0c` | yes | `origin/release-traindev-20261122` | 0 | retire; recovery: main @ 72373e0c |
| 79 | `~/agent_paper_B/.claude-worktrees/s2-audit-addendum-20261122` | `s2-audit-addendum-20261122` | `421dcfed` | yes | `origin/s2-audit-addendum-20261122` | 0 | retire; recovery: main @ 421dcfed |
| 80 | `~/agent_paper_B/.claude-worktrees/s2-rte-admit-20261121` | `s2-rte-admit-20261121` | `093fb6d1` | yes | `origin/s2-rte-admit-20261121` | 0 | retire; recovery: main @ 093fb6d1 |
| 81 | `~/agent_paper_B/.claude-worktrees/s2c3-deploy-20261116` | `s2c3-deploy-20261116` | `2b454c33` | yes | `origin/s2c3-deploy-20261116` | 0 | retire; recovery: main @ 2b454c33 |
| 82 | `~/agent_paper_B/.claude-worktrees/s2c3-driver-20261116` | `s2c3-driver-20261116` | `c545852c` | yes | `origin/s2c3-driver-20261116` | 1 | keep: uncommitted edits |
| 83 | `~/agent_paper_B/.claude-worktrees/s2c3-driver-fix-20261116` | `s2c3-driver-fix-20261116` | `1e3b0320` | yes | `origin/s2c3-driver-fix-20261116` | 0 | retire; recovery: main @ 1e3b0320 |
| 84 | `~/agent_paper_B/.claude-worktrees/s2c3b-fix-20261116` | `s2c3b-fix-20261116` | `f77612d1` | yes | `origin/s2c3b-fix-20261116` | 0 | retire; recovery: main @ f77612d1 |
| 85 | `~/agent_paper_B/.claude-worktrees/s2c3b-live-20261116` | `s2c3b-live-20261116` | `21b9f70d` | yes | `origin/s2c3b-live-20261116` | 1 | keep: uncommitted edits |
| 86 | `~/agent_paper_B/.claude-worktrees/s2c5-switch-20261116` | `s2c5-switch-20261116` | `ee2c2b5d` | yes | `origin/s2c5-switch-20261116` | 0 | retire; recovery: main @ ee2c2b5d |
| 87 | `~/agent_paper_B/.claude-worktrees/screen-measure-prep-20261126` | `screen-measure-prep-20261126` | `01e50def` | no | `origin/screen-measure-prep-20261126` | 0 | retire; recovery: origin/screen-measure-prep-20261126 @ 01e50def |
| 88 | `~/agent_paper_B/.claude-worktrees/sweep1-diag-20261122` | `sweep1-diag-20261122` | `a11b552d` | yes | `origin/sweep1-diag-20261122` | 0 | retire; recovery: main @ a11b552d |
| 89 | `~/agent_paper_B/.claude-worktrees/sweep2-auth-20261119` | `sweep2-auth-20261119` | `df58bcd5` | yes | `origin/sweep2-auth-20261119` | 0 | retire; recovery: main @ df58bcd5 |
| 90 | `~/agent_paper_B/.claude-worktrees/sweep2-auth-20261120b` | `sweep2-auth-20261120b` | `149a7b72` | yes | `origin/sweep2-auth-20261120b` | 0 | retire; recovery: main @ 149a7b72 |
| 91 | `~/agent_paper_B/.claude-worktrees/sweep2-cluster-20261116` | `sweep2-cluster-20261116` | `acae9fde` | no | `origin/sweep2-cluster-20261116` | 0 | retire; recovery: origin/sweep2-cluster-20261116 @ acae9fde |
| 92 | `~/agent_paper_B/.claude-worktrees/sweep2-int-main-20261120` | `(detached)` | `3a6dcf4d` | yes | `origin/HEAD`, `->` | 0 | retire; recovery: main @ 3a6dcf4d |
| 93 | `~/agent_paper_B/.claude-worktrees/sweep2-main-20261116` | `sweep2-main-20261116` | `d9ff7813` | yes | `origin/sweep2-main-20261116` | 0 | retire; recovery: main @ d9ff7813 |
| 94 | `~/agent_paper_B/.claude-worktrees/trackp-h200-20261118` | `trackp-h200-20261118` | `c33aa647` | no | `origin/trackp-h200-20261118` | 21 | keep: uncommitted edits |
| 95 | `~/agent_paper_B/.claude-worktrees/trackp-h200-clean-20261121` | `trackp-h200-clean-20261121` | `443855d5` | no | `origin/trackp-h200-clean-20261121` | 0 | retire; recovery: origin/trackp-h200-clean-20261121 @ 443855d5 |
| 96 | `~/agent_paper_B/.claude-worktrees/trackp-p3a-code-20261116` | `trackp-p3a-code-20261116` | `8662e359` | no | `origin/trackp-p3a-code-20261116` | 4 | keep: uncommitted edits |
| 97 | `~/agent_paper_B/.claude-worktrees/trackp-p3a-d2-20261119` | `trackp-p3a-d2-20261119` | `8309b69e` | no | `origin/trackp-p3a-d2-20261119` | 0 | retire; recovery: origin/trackp-p3a-d2-20261119 @ 8309b69e |
| 98 | `~/agent_paper_B/.claude-worktrees/trackp-p4-cluster-20261125` | `trackp-p4-cluster-20261125` | `8a9d48a1` | no | `origin/trackp-p4-cluster-20261125` | 0 | retire; recovery: origin/trackp-p4-cluster-20261125 @ 8a9d48a1 |
| 99 | `~/agent_paper_B/.claude-worktrees/trackp-v22-image-20261124` | `trackp-v22-image-20261124` | `a20bd02e` | yes | `origin/trackp-v22-image-20261124` | 0 | retire; recovery: main @ a20bd02e |
| 100 | `~/agent_paper_B/.claude-worktrees/trackp-v22-stop-20261123` | `trackp-v22-stop-20261123` | `91617ab4` | yes | `origin/trackp-v22-stop-20261123` | 0 | retire; recovery: main @ 91617ab4 |
| 101 | `~/agent_paper_B/.claude-worktrees/trackS-ops-20261030` | `trackS-ops-20261030` | `fab88fce` | no | `origin/mac-tracks-stop4-end-20261115`, `tasl2/trackS-ops-20261030` | 0 | retire; recovery: origin/mac-tracks-stop4-end-20261115 @ fab88fce |
| 102 | `~/agent_paper_B/.claude-worktrees/w2-3-check-20261115` | `w2-3-check-20261115` | `03d742cf` | no | `origin/w2-3-rebuild-unit-20261115` | 0 | retire; recovery: origin/w2-3-rebuild-unit-20261115 @ 03d742cf |
| 103 | `~/agent_paper_B/.claude-worktrees/w2-3-rebuild-unit-20261115` | `w2-3-rebuild-unit-20261115` | `2989f383` | no | `origin/w2-3-rebuild-unit-20261115` | 0 | retire; recovery: origin/w2-3-rebuild-unit-20261115 @ 2989f383 |
| 104 | `~/agent_paper_B/.claude-worktrees/xc3-short-verdicts-20261126` | `xc3-short-verdicts-20261126` | `ded282c8` | yes | `origin/xc3-short-verdicts-20261126` | 0 | retire; recovery: main @ ded282c8 |
| 105 | `~/agent_paper_B/.claude/worktrees/agent-a5b7dbe7d7174f30e` | `mac-p4-direct-20261126` | `bd594cfa` | no | no | 1 | keep: in active use (worker session or live agent) |
| 106 | `~/agent_paper_B/.claude/worktrees/agent-a7ef8fe12f98580a2` | `mac-d3c-memo-20261127` | `aacde378` | no | `origin/mac-d3c-memo-20261127` | 0 | keep: in active use (worker session or live agent) |
| 107 | `~/agent_paper_B/.claude/worktrees/agent-aa6344c5f691ec798` | `mac-d3-predecl-r4-20261127` | `0b373a79` | no | `origin/mac-d3-predecl-r4-20261127` | 0 | keep: in active use (worker session or live agent) |


14 further worktrees are session scratch trees under the system temp directory (paths not listed); each goes with its session.

