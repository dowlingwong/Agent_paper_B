# Paper B repository — independent review, 8 October 2026

Reviewer: a fresh agent session (AI-assisted review; **not** a human review).
Repository: `~/Documents/agent_paper_b`, built by copying Paper B out of
`~/Documents/GitHub/agent-checkpoint-intervention` at
`S = 4154f153` following Prompt 1 of
`docs/paper_split/B_REPO_PROMPTS_20261008.md` and the checklist
`AB_REPO_SPLIT_CHECKLIST_20261005.md`. Neither repository was modified; all
checks ran in fresh clones and `git archive` exports under a scratch directory.

Snapshot reviewed: `e494a4d` (six commits). Reference export: `git archive S`
under the same Python 3.13.15 interpreter.

## Findings

### BLOCKER

None.

### MAJOR

**M1 — `make smoke-b` fails on a clean checkout.**
`Makefile:19-20` runs `experiments/paper_b/smoke_b.py --output
results/paper_b/smoke_latest`, but that directory is tracked and inherited from
S, and `smoke_b.py` refuses to overwrite an existing output directory. Reproduced
in a fresh clone at `e494a4d`:

```
$ make smoke-b
refuse overwrite: results/paper_b/smoke_latest exists; choose a fresh directory
make: *** [smoke-b] Error 1
```

The README states that `make smoke-b` rewrites tracked files; it does not, it
refuses. Fix: remove the directory first (`rm -rf results/paper_b/smoke_latest`
before the run, then document restoring it with `git checkout --`), or point the
target at a fresh ignored directory and update the README.

**M2 — `docs/paper_split/RUNBOOK.md` has two dangling links.**
`RUNBOOK.md:30` links to
`../../archive/planning_2026-09-26/paper_split_reviews/CONTINUATION_2026-09-26.md`
and `RUNBOOK.md:432` links to `PAPER_A_TMLR_RUNBOOK.md`; neither target exists in
this repository. Task 2 requires links to Paper A documents and source-only files
to be rewritten as URLs into the source repository at S, with no dangling link.
Fix: replace both with
`https://github.com/dowlingwong/agent-checkpoint-intervention/blob/4154f153/<path>`.

**M3 — `docs/paper_split/VALIDATION.md` contains Paper A content.**
Task 2 says the B copy is B entries only, with no Paper A sentences. Lines 41,
47, 64 and 66 record Paper A commands and files: `make paper-a paper-b`,
`sh papers/paper_a/scripts/check_anonymity.sh --mode submission`, and
`33 measurement` tests. Fix: drop the A targets from the command lists (or
rephrase them as source-repository commands) and remove the measurement count;
the `paper_a/scripts/check_anonymity.sh` reference can point at the copied
`papers/paper_b/scripts/check_anonymity.sh` instead.

### MINOR

**m1 — `make paper-b` cannot build on this host.** `latexmk` is not installed,
so the PDF half of `make paper-b` fails (`make[1]: latexmk: No such file or
directory`). This is environmental, not a repository defect: the `verify` and
`anonymity-check` halves were exercised separately and pass, and
`check-release-b` records `pdf_skipped_no_latexmk`. The task's done-when
"`make paper-b` builds" is therefore not met locally. The rules forbid network
installs beyond locked test dependencies, so installing TeX is out of scope;
record the limitation (the build agent already does in `VALIDATION.md` §8).

**m2 — `docs/paper_split/OPEN_ITEMS.md:...` refers to `L1_BASELINE.md`, which
is not present.** The reference is plain text, not a markdown link, so the link
checker does not flag it, but it is a source-only file. Note that it lives in the
source repository (or point at it by URL).

**m3 — provenance notes are not always "two lines".** `RUNBOOK.md` starts with
an H1 title; its note is on lines 3-5. `CLAIMS.yaml` and `MIGRATION.yaml` use a
three-comment-line note. Functionally fine; a strict reading of task 2 wants the
note first and two lines. Low priority.

### NIT

**n1 — `scripts/make_release.py` retains unused helpers** `_iter_files` and
`_sha256` (lines 53 and 62); they were unused at S too.

**n2 — the allowlist test's local-module allowance** (`LOCAL_MODULES`, by file
stem) could mask a third-party module if a local file shadowed its name. The
explicit third-party set is small and correct for the current closure.

## What I checked and found correct

- **Completeness.** Every Phase 1 "move" and "copy" path and every live-lane item
  is present. All 1,622 tracked-at-S files in the copied path set are staged and
  byte-identical to the S export, except the files listed in `PROVENANCE.md`. The
  four tracked-but-gitignored files (`packages/ai/src/providers/data/*`,
  `doom.wasm`, two `.jsonl` fixtures) were force-added, as required.
- **Import closure.** An independent AST walk from `control/`,
  `experiments/paper_b/`, `tests/control/`, `launch_validator.py` and the copied
  scripts resolves every `causal_branch` import to a present module; no
  measurement-core or other missing module is referenced.
- **Nothing copied that should not be.** `papers/paper_a`, `protocols/paper_a`,
  `experiments/paper_a`, the measurement core, `state_audit.py`,
  `variance_adaptive.py`, `replay_validity.py`,
  `finite_repeat_identification.py`, `finite_budget_decisions.py`, `evidence/`,
  `archive/` and `experiment_scaffold/tests/` are all absent.
- **Standalone done-when.** In a fresh clone at `e494a4d`: `tests/control` 207
  PASS (matching the S export's 207); `tests/release` 6 PASS; `tests/standalone`
  8 PASS; the allowlist test fails on a real planted
  `import causal_branch.variance_adaptive` in `tests/control/test_tree.py`;
  `smoke_b.py` 11/11 with output byte-identical to S; v3 qualification refuses
  both lanes and v2 refuses every phase/lane, all byte-identical to S; `make
  release-b` builds 107 files; `make check-release-b` PASS with
  `control_tests_exit_zero` true; `make test` 207+6+8; anonymity PASS;
  `verify_vendored_pi.py` fails exactly as at S (three unexplained files).
- **Science untouched.** `experiments/paper_b/smoke_b.py` and
  `experiments/paper_b/task_cc/witnesses.py` hash to the contract pins
  (`f9aa1df5…`, `127fe8cd…`); `design_decisions_20260927.yaml` hashes to
  `61c97155…`; all are byte-identical to S. No estimand, controller, allocator,
  comparator, budget or contract value changed.
- **Release records.** `release/paper_b_manifest.json` is byte-identical to S;
  `release/check_release_b.json` differs only in the redacted host-path string,
  as listed.
- **Records.** The B copies carry provenance notes; `CLAIMS.yaml` holds B-C1…B-C7
  and the B prior-disclosure entry; `MIGRATION.yaml` holds the B and SHARED
  entries and parses; `PRIOR_DISCLOSURE.md` and `TKV2017_LESSONS.md` are whole;
  `STATUS.md` has no Paper A sentences; `OPEN_ITEMS.md` has B1-B6, the B
  decisions, the B housekeeping and a complete "Standalone repository" section
  against task 4.
- **PROVENANCE.md.** Source URL, S and date, the full path map, moved vs copied,
  every differing file with a path-only/tooling-only reason, and the licences
  present. Spot-checked: `third_party/pi/LICENSE` is MIT with digest `0457f5bc…`;
  `highlight.min.js` is BSD-3-Clause; `doom.wasm` is GPL-2.0 via `doomgeneric`;
  the copied schema is MIT (`da8dcbd1…`); the TypeSafe skill is MIT; `icml2026.bst`
  is LPPL. Kev/CLM are marked not re-checked, as allowed.
- **Hygiene.** Every commit is authored and committed by
  `Dowling Wong <wangdowling@gmail.com>` with `%G?` = `N` (no foreign
  signatures); every message ends with the AI-attribution trailer and names S and
  the source URL in the import commit. No credential files. No author host path,
  username, or home-directory / dataset-root / shared-storage prefix outside
  `third_party/pi/`; the remaining hits are upstream Pi examples/tests (listed in
  `VALIDATION.md`). No generated build products are tracked.

## Verdict

The repository is a faithful, self-contained copy with a working CPU path. Three
MAJOR items (M1, M2, M3) should be fixed before the repository is treated as
finished; none changes B's science. The remaining items are minor or
environmental.
