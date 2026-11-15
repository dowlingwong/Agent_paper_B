# W2 v3 Track P data rebuild — unit plan (15 November 2026, cluster agent; review required before running)

**Authority.** Author rows `R1-W2-3-STOP` and `R1-B2-REPAIR-SCOPE-ACK` (`author-ack-w23-20261115` @
`b0c8a48d`, PLAN §10); `reports/W2_V3_REBUILD_20261115.md` §2 (rebuild every Track P feature table and prompt
set from the branch, write `FEATURIZER_VERSION` and the prompt version into every table manifest, do not mix
v1/v2 prompts); the W2-3 PASS evidence on `w2-3-check-20261115` @ `03d742cf`.

**Host / inputs (read-only).** deepthought; the pinned sweep-1 index
`/ceph/dwong/…/agent_paper_B/results/r1/pilot/C3_sweep_index_20261028T033315Z.json` (SHA-256 `812468e2…`, the
`R1-DT-PIN-SWEEP1` file), its paper root, and the sweep-1 ledgers it names — opened read-only; `r1_sealed`
paths refused (by the reviewed `build_from_sweep`). The W2-3 PASS JSON
(`w2/w2_3_check_20261115.json`, SHA-256 `b11217d0…`) is an input to the manifest only.

**Code.** A clean checkout of the reviewed branch `mac-w2-v3-rebuild-20261115` @ `d8aa9561` (the W2-3 checker
branch, which also carries `FEATURIZER_VERSION = c3_features/v3` and `PROMPT_VERSION = trackp_prompt/v2`),
`git status` clean, HEAD verified.

**Command (the only data-producing step).**

```
cd <checkout> && PYTHONPATH=. python3 -B -m r1.c3.dataset build-sweep \
  --index <paper root>/results/r1/pilot/C3_sweep_index_20261028T033315Z.json \
  --paper-root <paper root> \
  --classification <paper root>/results/r1/evidence/C3_sweep_classification_20261028.json \
  --out <NEW versioned dir>
```

`--classification` implements the author's **R1-SWEEP1-CLASSIFY** row (the sweep-1 batch is the EVIDENCE batch;
the index's PILOT/ENGINEERING_ONLY strings are a runner defect), so the table label is `EVIDENCE` and the
EVIDENCE-only `table_sha256` provenance is produced; the sidecar is pinned at SHA-256 `bb6d891c…`. In this mode
the reviewed code creates the output directory itself (`mkdir(exist_ok=False)`), so the unit creates only the
parent (`tables/`) and writes the build stdout/stderr to a **separate** `logs/rebuild_<UTC>/` directory (outside
`OUT`); if the code refuses, the unit STOPs and reports why, preserving `OUT`/logs.

**Output (never overwrite).** A new directory `…/w2_3_rebuild_20261115/tables/c3_features_v3_<UTC>/` (the unit
creates it 0700 and refuses if it exists). It adds `manifest.json` with: `code_commit`, `featurizer_version`,
`prompt_version`, `prompt_version_mixing` statement, sweep-index path+sha, the W2-3 PASS evidence path+sha+status,
the table label/row/config/replay-check counts and the `build.json` sweep-index hash, the SHA-256 of
`proposals.jsonl`/`configs.json`/`build.json`, the v1-never-overwritten policy, and the version disclosure.
Then `SHA256SUMS` and an exclusive `REBUILD_OK`. v1 tables/outputs are never written; a new versioned dir is
the only destination.

**Review round 1 (W2_3_REBUILD_REVIEW_20261115.md) answers.** R1: classification mode with the pinned sidecar and
logs outside `OUT`; R2: `paper_root` is a recorded input parameter (with the output parent as a separate key);
R3: `PYTHONDONTWRITEBYTECODE=1` + `python3 -B` on every invocation (no `__pycache__` writes into the checkout);
R4: the mixing statement is scoped to the Track P table build path and the manifest discloses the budget-line
change and the synthetic exam's retained v1 budget line (W2-4 open); R5: `replay_checks_total == 288 × 20 = 5760`
is asserted and the evidence ledgers/runs/differing counts are recorded; R6: python/numpy versions, a ≥2 GiB
`df` preflight and the exact build command are recorded. NITs: `SHA256SUMS` is self-checked before `REBUILD_OK`,
the no-v1-token scan covers only the table files (the manifest disclosure names v1 legitimately), the unit-level
`r1_sealed` check is a lexical path check (the reviewed code's `refuse_sealed` covers inputs), and the repo W2-3
evidence path/SHA is recorded next to the `/work` copy.

**Version discipline.** The script reads `FEATURIZER_VERSION` and `PROMPT_VERSION` from the reviewed code and
refuses unless they are exactly `c3_features/v3` and `trackp_prompt/v2`; it also refuses if the code defines
more than one `trackp_prompt/v*` version, and after the build it refuses if any generated file mentions
`trackp_prompt/v1`. The disclosure line records that the sweep-1 ledgers are historical v1-code data that are
re-derived **read-only** into the v3 feature table, and that `trackp_prompt/v2` is the prompt version recorded
for downstream Track P prompt sets (no mixing).

**STOP conditions (preserve, report, no retry).** Wrong checkout HEAD/dirty checkout; sweep-index SHA mismatch;
missing paper root; W2-3 evidence SHA mismatch; output directory exists; `build-sweep` refuses or fails;
missing/empty table files; version mismatch; prompt-version mixing; manifest verification failure; any write
under `r1_sealed`. On a STOP the partial output directory is kept (moved aside only by the author/operator
decision; no deletion) and the reason is reported.

**Review gate.** This unit is submitted for independent review **before running** (author's instruction).
The reviewer should check: the pinned inputs/commit, the single data-producing command and that it is the
reviewed `build-sweep`; the output-isolation/never-overwrite logic; the manifest/version/mixing guards; the
read-only claim; and the STOP/no-retry/no-deletion behaviour. After acceptance the unit is run on deepthought
and its `build.stdout`/`build.stderr`/`manifest.json`/`SHA256SUMS` are reported.

**Not part of this unit.** Downstream Track P training (E0/training) stays blocked by the author's other gates
(Q-TORCH: L40S/H200 smoke + E0 equivalence + v2 digest approval); no data is written outside the new table
directory; no v1 table is modified.
