# Paper B repository — second independent review (AI-assisted), 8 October 2026

- **Reviewed:** `main` = `d09f1d1` (8 commits, `a93e2b7`…`d09f1d1`), clone of `~/Documents/agent_paper_b`.
- **Reference:** `S = 4154f15328ad7dc7119d306e16b472f1de6ca782`, exported with `git archive`.
- **Reviewer:** an AI agent in a fresh session (AI-assisted review, not a human review).
- **Method:** I modified neither repository. Every check ran in a fresh clone or an S export under `review2_b/`.
- **Environment:** Python 3.13.16 venv with the locked dependencies (numpy 2.3.0, scipy 1.18.1, scikit-learn 1.5.2, PyYAML 6.0.3, hypothesis 6.112.1), latexmk 4.83 / pdfTeX 1.40.25, git 2.43.
- **Verification:** I verified every finding against the sources. Findings I could not verify were dropped.

## 1. Findings

**Counts:** 0 BLOCKER, 1 MAJOR, 7 MINOR, 5 NIT.

### R2-B1 — MAJOR — `tests/standalone/test_import_allowlist.py:150-160` and `:36-49`

**Problem.** The test that replaced `check_split.py` misses the most common way to import a sibling module, and never walks the copied shared modules. Planted in a fresh clone, then `unittest discover -s tests/standalone`:

- **Not caught (suite OK):** `from causal_branch import variance_adaptive`, `from causal_branch import measurement` and `from .. import state_audit` in `control/allocation.py`; `import causal_branch.state_audit` in `checkpoint.py`; `from causal_branch.measurement import facade` in `pi_fork.py`.
- **Caught:** `import causal_branch.variance_adaptive`, `importlib.import_module('causal_branch.measurement')`, `import torchvision`, `import requests`, a literal `/etc/passwd` passed to `spec_from_file_location`.

Causes: an `ImportFrom` records only `node.module` (`causal_branch`), never `causal_branch.<name>`; `ROOTS` excludes `causal_branch/*.py` and `adapters/`. The `spec_from_file_location` check (`:229-237`) is vacuous on the real code: all four call sites pass `ROOT/'…'`, not a literal. `VALIDATION.md:84` ("rejects every planted forbidden import") overstates.

**Fix** (verified in a scratch clone: 8/8 OK on the current tree; all five plants then fail; `from causal_branch.types import X` and `from .. import types` still pass):

```diff
@@ ROOTS
     ROOT / "scripts/release_provenance.py",
+    *sorted((PKG / "causal_branch").glob("*.py")),
+    PKG / "causal_branch/adapters",
 ]
+def _is_submodule(package: str, name: str) -> bool:
+    if package != "causal_branch" and not package.startswith("causal_branch."):
+        return False
+    full = f"{package}.{name}"
+    if full in FORBIDDEN_CAUSAL_BRANCH:
+        return True
+    target = PKG.joinpath(*full.split("."))
+    return target.with_suffix(".py").is_file() or (target / "__init__.py").is_file()
@@ imports_from_source, ImportFrom branch
-                found.add(".".join(basepkg + ([node.module] if node.module else [])))
+                base_name = ".".join(basepkg + ([node.module] if node.module else []))
             elif node.module:
-                found.add(node.module)
+                base_name = node.module
+            else:
+                continue
+            found.add(base_name)
+            for alias in node.names:
+                if alias.name != "*" and _is_submodule(base_name, alias.name):
+                    found.add(f"{base_name}.{alias.name}")
```

Also add planted unit tests for the two `from` forms, optionally read the right-hand literal of `ROOT / "…"` in `dynamic_file_literals`, and correct `VALIDATION.md:84`.

### R2-B2 — MINOR — `scripts/check_release_independence.py:97-106, 126`

**Problem.** A host without latexmk gets a release PASS. I ran the check with latexmk removed from `PATH`:

```
check-release-b: PASS … pdf_skipped_no_latexmk: True   (exit 0)
```

- The key starts with `pdf_` and is `True`, so it counts toward the pass.
- At S, a missing latexmk aborted the check.
- The docstring (`:4`) still says the check "proves the package builds its PDF".
- `PROVENANCE.md:73` does not mention the skip, which commit `82c30a3` introduced.

**Fix.** Replace line 106 with:

```python
report["checks"]["pdf_built"] = False
report["checks"]["pdf_skip_reason"] = "latexmk not found"
```

Alternatively, allow the skip only behind an explicit `--allow-no-pdf` flag that prints `PASS (PDF not built)`. Update the PROVENANCE row either way.

### R2-B3 — MINOR — `docs/paper_split/VALIDATION.md:41, 47, 64, 66` (the M3 fix introduced this)

**Problem.** The ledger says "Only commands that were actually executed are listed" (`:6`). The M3 fix rewrote historical commands into ones that were never run:

- `make paper-a paper-b` became `make -C papers/paper_b verify` (B7 and F12).
- `sh papers/paper_a/scripts/check_anonymity.sh` became `sh papers/paper_b/scripts/check_anonymity.sh` (B1 and F11). That path did not exist at those commits.

**Fix.** Restore the commands as they were run and annotate them instead. For example:

- B1/F11: "`sh papers/paper_a/scripts/check_anonymity.sh --mode submission` (source repository; script now copied to `papers/paper_b/scripts/`)".
- B7/F12: "`make paper-a paper-b` (source repository; B half relevant)".

Keep the deletion of the measurement test count.

### R2-B4 — MINOR — `docs/paper_split/VALIDATION.md` (rows missing after `:47`); `STATUS.md`

**Problem.** The B copy drops the B rows L8, L9 and L10 and the `12507267` release row (S `VALIDATION.md:128-137, 259-263`). These are the only records of how tracked artefacts in this repository were produced:

- `results/paper_b/smoke_v2_20260926/`;
- `results/paper_b/tree_v1_20260926/`;
- `release/check_release_b.json` and `paper_b_manifest.json` (source `125072671c…`, 53 files, measurement core included).

STATUS also omits:

- S's "Version pointers" line ("B 53 files, source `12507267`");
- the B sentence of the 4 October "decisions adopted" entry.

**Fix.** Add a section "26 September (source `12507267`; L8–L10)" with the B halves of those rows:

- **L8:** `make smoke-b B_SMOKE_OUTPUT=results/paper_b/smoke_v2_20260926` → 9 engineering checks; 33 control and 5 release tests.
- **L9:** validator: engineering accepts, draft launch refuses; 43 control tests.
- **L10:** `tree_fixtures.py --output results/paper_b/tree_v1_20260926` → 8 ENGINEERING_ONLY trees; 49 control tests.
- **12507267:** `release-b` plus `check_release_independence.py --paper b` PASS, B 53 files.

Add the STATUS pointer as well.

### R2-B5 — MINOR — `release/check_release_b.json:13, 28`

**Problem.** Only the author home-directory string was redacted. Both `cwd` values still hold the author's macOS per-user temp path (`<tmp>/release-b-…/…`). The recorded host-path scan (`VALIDATION.md:96`) did not include the macOS temp-directory prefixes. In addition, every run of `make check-release-b` rewrites this tracked file with absolute paths; here I observed the reviewer's own interpreter path and `<tmp>/release-b-…/…`.

**Fix.**

- Replace both values with `<tmp>/release-b-…/paper_b` and `<tmp>/release-b-…/paper_b/papers/paper_b`.
- Extend the PROVENANCE row and add the macOS temporary-directory prefixes (`var/folders`, `private/var`) to the scan.
- In `_run`, record `cwd` relative to the package and `Path(sys.executable).name` (tooling-only).

### R2-B6 — MINOR — `PROVENANCE.md:57, 73-74, 89-93, 102`

**Problems.**

- `:57` says "Every file below is the only set that differs". `:91` lists `Makefile` and `README.md` as "New files not present at S". Both files exist at S (the root Makefile and README) and were replaced, so they belong in the differs table.
- `docs/paper_split/B_REPO_REVIEW_20261008.md`, added in `d09f1d1`, is not listed.
- `:73` omits the latexmk skip.
- `:74` omits the change to the package README text: `make_release.py:116` now calls `contract_v3.yaml` active instead of `contract_v2.yaml`. Meanwhile the validator still defaults to `contract_v2.yaml` (`launch_validator.py:17`) and `MIGRATION.yaml` still says "b_v2 is active".
- `papers/paper_b/scripts/check_anonymity.sh` is mode 100755; at S the source was 100644.
- `:102` calls `doom.wasm` "GPL-2.0". The binary's own notice says only "GNU General Public License", with no version.

**Fix.**

- Move `Makefile` and `README.md` to the differs table as "replaced (B-only)".
- Add the review file to the new-files list.
- Extend the rows for `:73` and `:74`.
- Note the mode change.
- Change the doom row to "GPL (version per upstream doomgeneric, not re-checked); corresponding source: github.com/ozkl/doomgeneric plus `doom/build.sh` and `doom/doomgeneric_pi.c`".

### R2-B7 — MINOR — `scripts/make_release.py:33-50, 125`

**Problem.** The package README lists "Python 3.11+, NumPy, PyYAML", and the package ships no `requirements.lock`. But `tests/control` needs `hypothesis` (`test_allocator.py:9`) and scikit-learn. I ran the package's tests with a Python that has no hypothesis:

```
Ran 194 tests … FAILED (errors=1) ModuleNotFoundError: hypothesis
```

**Fix.**

- Add `"requirements.lock",` to `PAPER_B_ALLOWLIST`. The package becomes 108 files.
- Change `:125` to `- Python 3.11+ and the pinned packages in requirements.lock (NumPy, PyYAML, scikit-learn, hypothesis)`.

### R2-B8 — MINOR — `papers/paper_b/Makefile:23-24` (M1 was applied only partly)

**Problem.** `make -C papers/paper_b smoke` still fails on a clean checkout:

```
refuse overwrite: ../../results/paper_b/smoke_latest exists
```

**Fix.** Insert this line before the run line:

```
rm -rf ../../results/paper_b/smoke_latest
```

### R2-B9 — NIT — `docs/paper_split/OPEN_ITEMS.md:138`

**Problem.** The line lists `make release-b` among the targets that rewrite tracked files. It does not. After `make release-b`, `git status` shows only the ignored `release/paper_b/`, which matches the README.

**Fix.** Drop `make release-b` from the sentence.

### R2-B10 — NIT — `README.md:26-30`; `.python-version`

**Problems.**

- The README recommends a virtual environment "outside the repository", but its commands create `.venv` inside it.
- `.python-version` pins 3.13.4, while every validation ran 3.13.15 or 3.13.16. On a host with pyenv and no 3.13.4, a bare `python3` fails.

**Fix.**

- Change the text to "A virtual environment at `.venv/` (ignored; the Makefile uses it automatically):".
- Either relax the pin to `3.13` (and record it in PROVENANCE) or document the pin in the README.

### R2-B11 — NIT — `.gitignore:49`

**Problem.** The inherited `*.jsonl` rule, whose only exceptions are under `evidence/**`, will silently drop B's governance ledgers (`events.jsonl`, `timing.jsonl`, `control/governance.py:39-40`) when live results are committed under `results/paper_b/`.

**Fix.** Add `!results/paper_b/**/*.jsonl`, or record the decision in OPEN_ITEMS.

### R2-B12 — NIT — `docs/paper_split/VALIDATION.md:89`

**Problem.** The row covers three v2 phases. Prompt 1 asks for every phase.

**Result here:** all five phases (engineering, qualification, pilot, main_collection, final_evaluation) × both lanes refuse with exit 1: 10/10, byte-identical to S.

**Fix.** Update the row.

### R2-B13 — NIT — record-keeping

**Problems.**

- The `RUNBOOK.md:1` note omits §1–§3 and §8, which the file keeps.
- The `a93e2b7` commit message names four path-only fixes. The commit also contains the `.gitignore` comment, four 27-September redactions and the v1-plan note. PROVENANCE does list them.
- First-round findings m1 and n2 were left unapplied with no recorded reason.
- `ALLOWED_THIRD_PARTY` (`test_import_allowlist.py:96`) lists the local module `release_provenance`.

**Fix.**

- Extend the RUNBOOK note.
- Add a "first-review dispositions" paragraph to the 8 October section of VALIDATION.
- Move `release_provenance` out of `ALLOWED_THIRD_PARTY`.
- No history rewrite is needed.

## 2. Dispositions of the first-round findings

| ID | Disposition | Evidence |
|---|---|---|
| M1 | Applied partly | `make smoke-b` gives 11/11, output byte-identical to S, and leaves `smoke_summary.json` modified as documented. The sub-Makefile `smoke` target still fails (R2-B8). |
| M2 | Applied correctly | RUNBOOK lines 29 and 431 are now `…/blob/4154f153/…` URLs. All 6 GitHub URLs in the records resolve to paths at S. No relative link dangles. |
| M3 | Applied, but the fix introduced a problem | See R2-B3. |
| m1 | Not applied (environmental) | On this host, `make paper-b` passes: 12 pp, 302,691 B, verify clean, anonymity PASS. Identical to the S build. |
| m2 | Applied correctly | `OPEN_ITEMS.md:155`. |
| m3 | Applied correctly | All 11 B copies begin with a two-line note. |
| n1 | Applied correctly | `_iter_files` and `_sha256` are gone; the package build is unchanged. |
| n2 | Not applied, no reason recorded | Confirmed: `import task` passes because a local `task.py` exists. Benign today. |

**VALIDATION.md (8 October) against my results:**

- **Matches:** 207/207 control tests; 6 release; 8 standalone; smoke 11/11 byte-identical; validator refusals byte-identical; release 107 files; `check-release-b` PASS with 207 control tests in the package; `make test`; anonymity; `verify_vendored_pi` failure identical; host-path list (12 `third_party` files for the home-directory prefixes).
- **Differs only by host:** `check-release-b` here built the PDF (`pdf_built: true`, 302,691 B); `make paper-b` passes here.
- **Overstated:** `:84` (R2-B1) and `:89` (R2-B12).

## 3. Push readiness

No BLOCKER for pushing to a new private GitHub repository.

- **Sizes.** The largest file is 2.37 MB (`before-compaction.jsonl`). The largest blob across all history is the same. The pack is 7.4 MiB. Nothing is near 50 or 100 MB.
- **Secrets.** No credentials, private keys or tokens. The only matches are upstream Pi placeholder API-key strings (an Anthropic-style test token and a Google-style test key). Prompt 1 says the same bytes were pushed to GitHub in the source repository on 7 October. `third_party/pi/.npmrc` holds no token.
- **Licences.** Kept: `third_party/pi/LICENSE` (MIT, `0457f5bc…`), the BSD-3 header in `highlight.min.js`, the TypeSafe `LICENSE` (MIT), the LPPL header in `icml2026.bst`, the MIT header in `reliability_schema` (same author). `doom.wasm` (GPL) is harmless in a private repository; add the corresponding-source pointer (R2-B6) before any public release. The repository has no top-level licence; that is the author's choice if it goes public.
- **`.gitignore`.** It covers the LaTeX intermediates, `__pycache__`, `.venv` and `release/paper_b/`. `git status --ignored` after all targets shows only ignored products plus the documented tracked rewrites. There is no `.hypothesis/` directory.
- **Config.** No absolute paths in `pyproject.toml`, `Makefile`, `skills-lock.json` or `experiment_scaffold/pyproject.toml`. No URL placeholders. The only source URL is in PROVENANCE and the README, as intended. I could not inspect the author's `.git/config`: this clone's `origin` is the transfer bundle.
- **Fresh clone elsewhere.** The CPU checks need no Node (`tests/control` 207/207 with Node off `PATH`); `make paper-b` needs latexmk, `pdfinfo` is optional. Hazards: `.python-version` 3.13.4 under pyenv (R2-B10), a CI without TeX passing the release check (R2-B2), and the package's missing requirements (R2-B7). The dangling `pi_extensions/node_modules` symlink is identical at S.

## 4. Checks run (B = fresh clone at `d09f1d1`; S = `git archive 4154f153`)

| Check | B | S reference |
|---|---|---|
| Tracked files / blob identity | 1,639 tracked: 1,607 blob- and mode-identical to S; 26 differ; 6 new | — |
| Expected Phase 1 and live-lane path set | 1,631/1,631 present | — |
| Transitive AST import closure (4 roots + 8 scripts + 12 Pi modules) | as stated in Prompt 1 (core 7 files, 12 live-lane modules, 8 server-start modules; numpy, yaml, sklearn, hypothesis; torch and clm lazy); all present | identical |
| `unittest discover -s tests/control` | 207 OK (same test IDs) | 207 OK |
| `tests/release` / `tests/standalone` | 6 OK / 8 OK | 5 OK / — |
| `smoke_b.py --output <scratch>` | 11/11; `diff -r` identical | 11/11 |
| `make test` / `make smoke-b` | 207 + 6 + 8 OK / 11/11 | — |
| Validator: v3 qualification, both lanes; v2 five phases × two lanes | 12/12 exit 1; byte-identical | identical |
| `make paper-b` | exit 0, 12 pp, verify clean, anonymity PASS | 12 pp, clean |
| `make release-b` / `make check-release-b` | 107 files / PASS, `pdf_built` 302,691 B, smoke and control exit 0 | — |
| Package `tests/control` without `PYTHONPATH` | 207 OK (194 + error without hypothesis) | — |
| `verify_vendored_pi.py` | exit 1; JSON identical; 3 unexplained files | exit 1 |
| Release anchor mutation (check removed) | `tests/release` FAILS (good) | — |
| Pinned SHA-256 | `smoke_b.py` `f9aa1df5…`, `witnesses.py` `127fe8cd…`, `design_decisions_20260927.yaml` `61c97155…` all match | — |
| Identity | 8/8 commits author = committer = Dowling Wong <wangdowling@gmail.com>; `%G?`=N; no `gpgsig` | — |
| Force-added files | 43 tracked-but-ignored, all tracked at S | — |

## 5. Checked and found correct

- **Science untouched.** `protocols/paper_b/`, `experiments/paper_b/`, `tests/control/`, `results/paper_b/`, every copied `causal_branch` file and `release/paper_b_manifest.json` are byte-identical to S. The 26 differing files are path-only or tooling-only.
- **Copied files.** `check_anonymity.sh` and `pi_model_data_provenance.json` are byte-identical to their S sources. The v3.1 plan equals the author's uncommitted original plus the note.
- **Nothing extra copied.** No Paper A paper, measurement core, evidence, protocols or experiments.
- **Records.** `CLAIMS.yaml` (B-C1…B-C7 and the B prior-disclosure entry) and `MIGRATION.yaml` (114 B + 5 SHARED) equal S. STATUS has no Paper A sentences. OPEN_ITEMS covers every Prompt 1 task 4 item; the six missing `RUNTIME_GLOBS` files and the absent `B_INFRA_RUNBOOK_20261005.md` are confirmed.
- **Other.** `start_bound_server.py:83` overrides the `run_local_soak.py` placeholder. Every commit ends with the AI-attribution trailer; the import commit names S and the source URL.
