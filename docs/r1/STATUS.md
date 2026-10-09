# Paper B (route R1) — status log

Newest entry first. Only this file says what is done.

## 9 October 2026 (evening) — build batch 1: L1

**L1 — Housekeeping.**
- **Paper B commit.** One commit, "Archive old Paper B plans; adopt route R1 canonical plan": the deletion of `docs/paper_split/`, the new `archive/old_b_2026-10-09/` and `docs/r1/`, the `README.md` banner, and the dated author decisions in PLAN §10 (D1, D3, D4, D14, D19, D20 — "decided 9 Oct 2026 by the author"). Pushed.
- **Harness.** Branch `r1` created from `main` at `da8dcbd` (the base commit). `uv sync --extra dev` succeeded. The `harness/claw-code` submodule is **not** initialised (D19).
- **Baseline test result** (`uv run python -m pytest --continue-on-collection-errors -p no:cacheprovider -q`): **277 passed, 9 failed, 1 error, 2 subtests passed**. Pre-existing, recorded not fixed:
  - `tests/test_artifact_completeness_and_manifest.py` ×4 (missing checked-in campaign report / manifest entries);
  - `tests/test_kdd_paper_sections.py` ×5 (the `paper/kdd_aae_2026/sections/*.md` files are absent);
  - `tests/test_legacy_noop_skip.py` error (imports `src.autoresearch_worker` from the uninitialised `harness/claw-code` submodule).

## 9 October 2026 (15:45) — build runbook and first prompt

Added `docs/r1/BUILD_RUNBOOK.md`, a per-step specification for L1–L14 written against the harness at `da8dcbd`, and `docs/r1/prompts/BUILD_BATCH1_PROMPT.md`, which covers L1, L3, L5 and L6 with the L2 defaults in an editable block. Nothing has been implemented yet.

## 9 October 2026 (15:30) — execution order adopted

RUNBOOK §3 gains the local-first order: build steps L1–L14 on the Mac, then experiments E1–E8. The next step is L1.

## 9 October 2026 (15:20) — configurator: encoder proposal

PLAN §7 is revised. The proposed primary is now a ModernBERT-family encoder decision model (Laya checkpoint vs plain ModernBERT-large), with late fusion of numeric features. Training is supervised, then an RL step with an RLCR-style bounded proper-score reward. Kev moves to the decoder comparison. D16 stays open.

## 9 October 2026 (afternoon) — format, benchmarks, configurator proposal

- **Author decisions:**
  - No manuscript format is fixed yet (R1-FORMAT).
  - ResNet-trigger is removed; experiments and configurator training use agent benchmarks across the board (R1-BENCH).
- **New open decision D20:** the benchmark set and scope. The proposal is in PLAN §6.
- **PLAN §7 gains** a verified candidate table and a proposed primary: Kev typed decision model; CLM, generative LLM and tabular as ablations. D16 stays open for discussion.

## 9 October 2026 (later) — venue, ledgers, harness clone

- **Author decisions:**
  - TMLR is the primary venue, with an ICML main-track quality bar (PLAN §9; D17 closed).
  - The original 1,355-trial ledgers are lost (D12 closed). Only aggregate tables survive, in the workshop-paper repo.
- **Harness clone.** `dowlingwong/autoresearch_harness` was cloned to `~/Documents/autoresearch_harness` at `da8dcbd`. The folder the author connected, `~/Documents/A-Governed-Harness-for-Auditable-LLM-Driven-ML-Experimentation`, is the workshop-paper repo (camera-ready; also the harness's submodule), not the harness code.
- **Note for the author.** Because the ledgers are lost, the `ClawWorker` `1 − val_bpb` sign issue cannot be checked for the workshop paper's autoresearch trials.
- **New default D14:** harness work on branch `r1` of that clone (confirm).
- **New open decision D19:** worker backend.

## 9 October 2026 — route R1 adopted; old plans archived; canonical plan written

- **Author decisions** (PLAN §1):
  - R1-ROUTE
  - R1-VENUE: rolling journal; TMLR recommended, to be confirmed as D17
  - R1-CARRY
  - R1-ARCHIVE
  - R1-PLAN
- **Archive.** All of the old `docs/paper_split/` moved to `archive/old_b_2026-10-09/docs_paper_split/`. The move includes the uncommitted §19 and §20 additions of 9 Oct and the 9 Oct prompt pack. Legacy code and the old manuscript stay in place for now (PLAN §8; RUNBOOK 0.1 decides).
- **New files:**
  - `docs/r1/PLAN.md`
  - `docs/r1/RUNBOOK.md`
  - this STATUS
  - `docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md`
  - `docs/r1/inputs/NOVELTY_SWEEP_20261009.md`

  The two inputs are AI-assisted subagent outputs and were not independently reviewed. In the sweep, three arXiv entries were spot-checked against their abstract pages (2607.05458, 2603.24647, 2608.21027). COTA's "0.5B" size is not stated on its arXiv page.
- **Not committed.** The file moves were made in the working tree with `mv`; nothing is committed yet. The first Phase 0 session commits them as one change: "Archive old Paper B plans; adopt route R1 canonical plan".
- **Next:** Phase 0 (RUNBOOK §3). The first prompt covers 0.1–0.3.
- **Open:**
  - D1–D12 and D14–D18 (PLAN §10);
  - the configurator architecture discussion (D16);
  - venue confirmation (D17).
