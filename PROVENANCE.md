# Provenance

- **Destination:** [Agent_paper_B](https://github.com/dowlingwong/Agent_paper_B).

This repository was created on 8 October 2026 by copying Paper B out of the
joint Paper A/B repository. The source repository is unchanged.

- **Source:** <https://github.com/dowlingwong/agent-checkpoint-intervention>
- **Snapshot:** `S = 4154f15328ad7dc7119d306e16b472f1de6ca782` (7 October 2026)
- **Method:** `git -C <source> archive S -- <paths> | tar -x` plus one untracked
  file (see below). The destination is a fresh git repository; it does not carry
  the source's history.

## Path map

### Moved (B only; these are removed from the source repository in Phase 3, after Paper A is submitted)

| Path | Notes |
|---|---|
| `papers/paper_b/` | including `legacy/` and `archive/` |
| `protocols/paper_b/` | |
| `experiments/paper_b/` | |
| `experiment_scaffold/src/causal_branch/control/` | including `configurator/` and `reliability_schema/` |
| `tests/control/` | |
| `results/paper_b/` | |
| `release/check_release_b.json`, `release/paper_b_manifest.json` | historical records kept as at S |
| `docs/paper_split/` B design and review records | `B_CONTROLLER_DESIGN_20260927.md`, `B_DECISIONS_20260927.md`, `B_NOVELTY_MEMO.md`, `B_DAC_CONFIGURATOR_AMENDMENT_20261004.md`, `B_READINESS_AUDIT_20261004.md`, `TASK_REALISM_REPORT.md`, `N1_DISPLACEMENT.md`, `FIX_QUEUE_20260927.md`, `FIX_REPORT_20260927.md`, `INDEPENDENT_REVIEW_20260927.md`, `REVIEWER_PROMPT_20260927.md`, `SELF_REVIEW_20260927.md`, `FINAL_REPORT_20260927.md`, `L8_EVALUATOR_REPORT.md` |

### Copied (shared; they also stay in the source repository)

| Path | Notes |
|---|---|
| `experiment_scaffold/src/causal_branch/__init__.py`, `types.py`, `branching.py`, `checkpoint.py`, `pi_fork.py` | import closure of B's code |
| `experiment_scaffold/src/causal_branch/adapters/__init__.py`, `adapters/toy.py` | import closure |
| `experiment_scaffold/pyproject.toml` | scaffold build metadata |
| Live-lane Pi modules | `adapters/pi_agent.py`, `budget.py`, `d7_adjudicator.py`, `history_retention.py`, `model_client.py`, `pi_models.py`, `pi_rpc.py`, `registered_tools.py`, `runtime_identity.py`, `substrate_identity.py`, `tool_socket.py`, `pi_fork.py` |
| Server-start / card-availability dependencies | `device_mapping.py`, `process_fleet.py`, `round4_qualification.py`, `round5_titan_exam.py`, `round5_titan_runtime_evidence.py`, `round5_titan_stage_a_acquisition.py`, `round5_titan_stage_b_execution.py`, `d7_registered_commands.py` |
| Vendored Pi | `third_party/pi/`, `experiment_scaffold/pi_extensions/`, `scripts/verify_vendored_pi.py`, `scripts/pi_pristine_manifest.txt`, `protocols/pi_local_modifications.yaml` |
| Live scripts | `scripts/run_local_soak.py`, `scripts/start_bound_server.py`, `scripts/e0_card_availability.py`, `scripts/resolve_pinned_node.py` |
| Release tooling | `scripts/make_release.py`, `scripts/check_release_independence.py`, `scripts/release_provenance.py`, `tests/release/` |
| Anonymity script | `papers/paper_a/scripts/check_anonymity.sh` copied to `papers/paper_b/scripts/check_anonymity.sh`; `papers/paper_a/` itself is not copied |
| Environment | `requirements.lock`, `pyproject.toml`, `.python-version`, `.gitignore`, `skills-lock.json` |
| Skill | `.agents/skills/typesafe-ai/` |
| Provenance record | `evidence/spikes/r8-pi-model-data-provenance/provenance.json` copied to `protocols/pi_model_data_provenance.json` |
| Shared records | B copies under `docs/paper_split/` (see below) |
| Plans | `B_INFRA_CONSTRUCTION_PLAN_20261005.md` (committed) and `B_INFRA_CONSTRUCTION_PLAN_20261006.md` (uncommitted in the source working tree at S) |

### Not copied

Paper A's paper (`papers/paper_a/`), its results, evidence, protocols and
experiments; the measurement core (`measurement/`, `state_audit.py`,
`replay_validity.py`, `finite_repeat_identification.py`,
`finite_budget_decisions.py`, `variance_adaptive.py`); the evidence tree; the
round 4–10 archives; and the tests for the copied Pi stack
(`experiment_scaffold/tests/`).

## Files that differ from S

Every file below is the only set that differs from the snapshot. Changes are
path-only or tooling-only; none touches B's science (estimands, outcome U,
controllers, allocator, comparators, budgets, contract values or the
SHA-256-pinned fixtures).

| File | Reason |
|---|---|
| `.gitignore` | comment naming an author dataset path replaced with a neutral phrase, and a `!results/paper_b/**/*.jsonl` exception added for B's governance ledgers (path/tooling-only) |
| `Makefile` | root Makefile replaced with B-only targets (tooling-only) |
| `README.md` | replaced with this repository's README (tooling-only) |
| `docs/paper_split/B_INFRA_CONSTRUCTION_PLAN_20261005.md` | provenance note prepended |
| `docs/paper_split/FIX_QUEUE_20260927.md` | author host path and username redacted (path-only) |
| `docs/paper_split/FIX_REPORT_20260927.md` | author host path redacted (path-only) |
| `docs/paper_split/INDEPENDENT_REVIEW_20260927.md` | author name/username/host path redacted (path-only) |
| `docs/paper_split/REVIEWER_PROMPT_20260927.md` | author host path redacted (path-only) |
| `papers/paper_b/Makefile` | `anonymity-check` points at the copied `scripts/check_anonymity.sh`; `smoke` removes the tracked `smoke_latest` first (path/tooling-only) |
| `pyproject.toml` | `testpaths` set to this repository's test directories (tooling-only) |
| `release/check_release_b.json` | the author host path in the recorded command and both `cwd` values redacted (path-only) |
| `scripts/check_release_independence.py` | B-only; control-test step, measurement-core check, relative `cwd` recording, and the `--allow-no-pdf` opt-out (tooling-only) |
| `scripts/make_release.py` | B-only allowlist (measurement core dropped, closure modules and `requirements.lock` added) and the package README contract/requirements text (tooling-only) |
| `scripts/release_provenance.py` | anchored on `papers/paper_b/main.tex` (tooling-only) |
| `scripts/run_local_soak.py` | author-specific binary default replaced with a neutral placeholder (path-only) |
| `scripts/verify_vendored_pi.py` | provenance record read from `protocols/pi_model_data_provenance.json` (path-only) |
| `tests/release/test_provenance.py` | B anchor plus a negative test for a missing manuscript anchor (tooling-only) |

### B copies of the shared records (new content at paths that exist at S)

`docs/paper_split/RUNBOOK.md`, `STATUS.md`, `VALIDATION.md`, `OPEN_ITEMS.md`,
`SCOPE.md`, `PRIOR_DISCLOSURE.md`, `CLAIMS.yaml`, `MIGRATION.yaml` and
`TKV2017_LESSONS.md` keep the Paper B sections only (or the whole file for
`PRIOR_DISCLOSURE.md` and `TKV2017_LESSONS.md`), each with a provenance note.
Links to Paper A documents and source-only files point into the source
repository at S.

### New files not present at S

`PROVENANCE.md`, `tests/standalone/test_import_allowlist.py`,
`papers/paper_b/scripts/check_anonymity.sh` (copied from another path; the source
was mode 100644 and it is stored here as 100644),
`protocols/pi_model_data_provenance.json` (copied from another path),
`docs/paper_split/B_INFRA_CONSTRUCTION_PLAN_20261006.md` (untracked in the source
working tree at S), and the two AI-assisted review records
`docs/paper_split/B_REPO_REVIEW_20261008.md` and
`docs/paper_split/B_REPO_REVIEW2_20261008.md`.

## Licences actually present

| Component | Licence | Evidence |
|---|---|---|
| `third_party/pi/` | MIT | `third_party/pi/LICENSE` (Copyright 2025 Mario Zechner; SHA-256 `0457f5bcec3b3b211605dfb5d1a49042fd638f3686a410fe099c24a25af13c48`, per the vendor verifier) |
| `third_party/pi/.../doom-overlay/doom/build/doom.wasm` | GPL (version per upstream doomgeneric, not re-checked) | built from `doomgeneric` (github.com/ozkl/doomgeneric) via `doom/build.sh` and `doom/doomgeneric_pi.c`; the binary sits in an example extension only |
| `third_party/pi/.../src/core/export-html/vendor/highlight.min.js` | BSD-3-Clause | licence header in the file (Highlight.js v11.9.0) |
| Copied harness schema (`control/reliability_schema/`) | MIT | header in `events.py` and `adjudication.py`; upstream commit `da8dcbd1a9821b852173cbe4805dbd1304ba1d17` |
| Kev (`jaredpalmer/kev`) and CLM (`Contrastive-LM/CLM`) | Apache-2.0 as stated in plan v3.1 | licence files are not in this repository — **not re-checked** |
| `.agents/skills/typesafe-ai/` | MIT | `LICENSE` (Copyright 2026 TypeSafe AI) |
| `papers/paper_b/icml2026.bst` | LPPL | licence header in the file |
| `papers/paper_b/icml2026.sty` | ICML 2026 kit (treated as LPPL with the kit) | the file header does not state a licence — **not re-checked** |

No other licence file is present in the repository.
