# Portal proposer exam — Phase 1 code handoff

26 October 2026. AI-assisted. ENGINEERING_ONLY / DRYRUN. Independent review pending; STOP 1 remains closed.

The author corrected storage to `/home/dowling/exam-x/models` and `/home/dowling/exam-x/work`. PLAN §10 and STATUS record this correction, the 100 GB decimal free-space floor, licence approvals, removal of unreleased Ornith-31B without a replacement, Mac-to-portal SSH bare-repository transfer, and permitted user-level uv/Python installation. No portal installation, code transfer, model-weight download, LLM inference, or evidence campaign was performed in Phase 1.

## Review scope and commits

Both repositories use `exam-x-20261026`. Paper baseline `8304156`; author decisions `acf0426` and `ef2377a`; frozen rule commit `4b9c656`; implementation `e6f42c0`. Harness baseline `6afdb0e`; implementation `897d83c8efa364ec2fdd37288241cc42e01d7274`. `HARNESS_PIN_EXAM` and the prospective `HARNESS_PIN_C3` bind that harness commit. Merge the accepted harness branch before the paper branch; only the author/coordinator merges protected branches.

The rule bytes and digest were committed before any B1 dry run. All existing B1 outputs are explicitly synthetic DRYRUN fixtures. The author has not yet accepted the rule hash into the scientific authorization row.

## Implementation map

| Gap | Implementation and verification |
|---|---|
| 1.1 | Harness provider response format and strict manager parser; six ordered string fields, no key/value enums. Opt-in collector/liveness/sweep propagation. HTTP fake tests cover malformed replies, no heuristic fallback and historical free parsing. |
| 1.2 | Dedicated service thinking flags/policies; reasoning excluded from proposal content; token telemetry and policy recorded. Fake server covers control flags. Actual pinned-build grammar compatibility remains Stage A work. |
| 1.3 | Harness `RandomValidManager`; all active editable keys and declared value grids, seeded by instance/trial. Determinism/active-key tests. |
| 1.4 | Exam self-forecast side query using typed A4 parsing. Harness reserves and charges observer calls; decisions never read forecasts. Fixed-clock test compares actual ledger bytes with/without observation. |
| 1.5 | Recursive EXAM label/seed guard in C3 build/build-sweep and sweep runner. Tests also reject unlabelled exam-seed campaign IDs. |
| 1.6 | Registry contains 21 candidates, three anchors, separate OLMo Think sensitivity, public pinned template/sampling metadata. Attention, sliding, hybrid fit estimates have three hand calculations and boundary tests. |
| 1.7 | Licence/source/occupancy blockers, Wilson, numeric paired-instance bootstrap and frozen digest. Numerical conformance checked against archived machinery; no archived performance results reused. |
| 1.8 | `exam_runner.py` stage-a/b1/b2; dedicated hash/build-pinned service; qualification before footprint adoption; host/disk/watchdog/namespace/author gates; root evidence certificates, whole-root interruption archive and resume. Fake end-to-end Stage A plus two-node B1 uses two fake candidates and all three anchors, with one worker kill/resume and thinking sensitivity. |
| 1.9 | Frozen `x5_rule_v1.yaml` and hash; Stage A intervals, B1 instance-cluster analysis/finalist rule, B2 final-Y reporting. Synthetic manifest tests. Raw audit arrays checked against reported deltas/Y. Author choices remain pending. |
| 1.10 | `configs/exam_portal.json`; ctx 32768/q8_0/ngl999/temp0.2/schema. Common host placeholders block production, phase-specific placeholders are checked only when their phase needs them. |

## Reproduction

Scratch environment `/private/tmp/exam-x-20261026/venv`, CPython 3.13.4. Frozen dependency export and baseline transcripts are under `docs/r1/reports/exam_phase1_20261026/`. No repo virtual environment or system Python changed. Run each suite from its repository, with the scratch interpreter on PATH and harness `src` on PYTHONPATH (paper root also on PYTHONPATH for paper):

```sh
python -m pytest -p no:cacheprovider --continue-on-collection-errors -q -ra
python -m r1.scripts.exam_runner --check-config --allow-placeholders
python -m r1.scripts.exam_dryrun --root /private/tmp/exam-x-NEW-UNIQUE
```

Set `PYTHONDONTWRITEBYTECODE=1`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`. Local socket/subprocess checks need normal host permissions. Fake dry runs refuse portal/Ada hosts and require a fresh marked temporary child directory. They do not load model tensors or produce scientific scores.

## Validation status

Authoritative before baselines: paper **417 passed, 22 failed, 9 skipped**; harness **448 passed, 8 failed, 1 collection error**. Exact failures and environment are preserved in `BASELINE.md` and the two baseline logs. Post-change full-suite results and reviewer verdict are pending. Counts must be compared by exact failure ID, not described as an all-green suite.

## Remaining phase gates

Phase 2 resolves vendor-first Q4_K_M sources (Ornith-35B vendor GGUF first; bartowski imatrix only if vendor unavailable; gpt-oss native MXFP4), full hashes/revisions/sizes, llama.cpp build/binary pins and OpenML cache provenance. Do not treat registry metadata or a fit estimate as model qualification. `requirements-host.in` is a declaration for later pinned resolution on portal, not an installed runtime.

Stage A requires a committed 50-prompt set reconstructed from real memory-on ledgers across at least four nodes; `freeze_prompts.py` verifies ledger/context hashes and refuses overwrite. Its independent exact-flag qualification measures footprint before the actual full-context/template/grammar/reproducibility probes. A 16k-only model is flagged for CPU-pool rows. Source/telemetry/dependency preparation failures STOP rather than excluding a candidate.

B1 requires the author-recorded rule hash and committed authorization note, three protocol nodes, seeds9001–9004, W20, audits9101–9104 and an author-bound LLM-call cap. Later config placeholders deliberately remain unresolved. B2 additionally needs the author count from B1 variance and a fresh authorization. Machine-readable authorization can be a plain JSON document or a single fenced JSON block in the Markdown note, with `author`, `phase`, `approved`, `rule_sha256`, `llm_call_cap`, `nodes`, `stage_a_table_sha256`, and for B2 `instances_per_node` plus `b1_analysis_sha256`. A Track G node requires the author addition and portal fit. D22/free-generation sensitivity is separate and follows the author-recorded D22 choice. No default author decision is inferred from code or test success.

At STOP 1 the independent reviewer must rerun both suites and the fake dry run, write `docs/r1/reviews/EXAM_1_REVIEW_20261026.md`, and accept fixes. The implementation agent cannot accept its own phase. Phase 2 and protected merges have not been started.

Review fixes preserve zero-audit diagnostics; enforce Stage A thinking exclusions in B2; bind upstream source hashes to resume/config/authorization; expose primary A4 forecast coverage, all-mode query failures and five fixed descriptive calibration bins. Evaluation of `p_no_effect` is explicitly pending an author outcome definition; no scientific no-effect threshold was invented.
