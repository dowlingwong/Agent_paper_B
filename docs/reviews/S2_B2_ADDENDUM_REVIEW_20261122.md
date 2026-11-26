# Independent review — filled sweep-2 B.2 audit addendum (publication readiness)

**VERDICT: NOT ACCEPTED** for publication as the branch stands. Everything in the addendum itself passes — code
acceptance, content vs code/draft, the four pins against the live deepthought artifacts, the D1 start row, and the
independence checks — but one evidence-completeness blocker and one workspace blocker must be cleared, plus one
front-matter edit should be made at signature (listed under Findings). No content re-review is needed after the
log fix: the addendum and review bytes are unchanged by it.

**Round 2 update (same day):** after the publication fixes at **`264896bb`** the two blockers below are cleared and
the addendum is **publishable with `approved: true` and the D1 start row** — see the Round 2 section at the end
(which also records two claimed minor edits that are not in the commit bytes).

Reviewer: independent reviewer (`reviewer-s2-addendum`), read-only. Date: 22 November 2026 (CET).
Reviewed target: `s2-audit-addendum-20261122` @ **`533b06ed`** (worktree `.claude-worktrees/s2-audit-addendum-20261122`;
base published `main` **`9c2979a2`**). Only this review file was written; no repository, git or deepthought write was
made by me, and no label, evaluation or sealed-output file was read.

**Files reviewed.** `docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md` (6,472 B, 69 lines, blob
`8ed780f7`, sha256 `0c01786447c15f884cbb3b17e0b61c65db839c59ff936a8e593b77aca7aa5fd1`, `approved: false` at line 13);
`docs/r1/reports/s2_audit_20261121/S2_B2_ADDENDUM_20261122.md`; `docs/r1/reports/s2_audit_20261121/
PRECONDITION2_20261122.md` and `precondition2/`; `docs/r1/reviews/S2_AUDIT_PRECONDITION2_REVIEW_20261122.md`
(12,609 B, sha256 `9aafa1f219d0d226fc2cb172f97cb36923fa394edcd857ebd03a2019f053bc6c`); `r1/c3/audit.py`
`b2_addendum` / `_sweep2_pins_match` / `sweep2_harness_equivalence`; draft
`docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md`; PLAN rows `R1-SWEEP2-B2-DECISIONS` (published at
`9c2979a2`) and the proposed `R1-SWEEP2-B2-GO` text (D1). Branch adds exactly 8 files over base `9c2979a2` (the
addendum, the two reports, the four `precondition2/` metadata files, the review); no other path changed.

## Bottom line on the addendum's substance

The filled addendum is internally consistent with the code and the draft, its counts/projection are correct, its four
pins equal the actual deepthought artifacts, and the code accepts `approved: true` + the D1 row in an independent
throwaway "published main" while refusing every negative control. The only content-level defects are non-blocking
compressions of the draft's STOP list and the untouched draft framing (Findings MINOR 1–3). The publication blockers
found are evidence/workspace-level: the four precondition-2 logs are gitignored and absent from the commit, and the
local branch ref has been advanced past `533b06ed` by an external simulation commit.

## 1. Code acceptance with `approved: true` and a simulated published `main` — PASS

I built my own throwaway copy, not the reviewed branch and not the pre-existing simulation described in Finding 5:
`git -C <worktree> archive 533b06ed | tar -x` into `/tmp/s2_b2_addendum_review_20261122/repo`, `git init -b main`,
commit f56bc822; then (a) `approved: false` → `approved: true` in the addendum key block only, (b) the D1
`R1-SWEEP2-B2-GO` row inserted verbatim (see §4), commit **`51cf6fad68669b29e2e8e30be0d10b9f2c2f42b6`**; a local bare
`origin` (`/tmp/s2_b2_addendum_review_20261122/origin.git`) whose `main` = `51cf6fad…` (pushed and fetched; `git
ls-remote` = `refs/remotes/origin/main` = `51cf6fad…`). The precondition-2 review was already in the `533b06ed` tree
at the expected path, untouched.

Call (numpy-enabled interpreter `.claude-worktrees/_harness_venv/bin/python`, 3.11.11 / NumPy 2.4.6; the code paths
called here are pure git/hash logic, `requires-python = ">=3.11"`): `r1.c3.audit.b2_addendum(root,
'docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md', 'db7f344d6ac372737444db5ab036d370543ea65f', 'sweep2')`
returns **ACCEPT** (rc 0):

```json
{"path": "docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md",
 "pins": {"sweep2_index_sha256": "b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4",
          "sweep2_extract_sha256": "82c7605291cc07d5d06dc610c6f9a34e6e8d417e62cadb7de7ca59d7b103a4da",
          "table_proposals_sha256": "379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9",
          "table_configs_sha256": "de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d"},
 "precondition2_review": {"path": "docs/r1/reviews/S2_AUDIT_PRECONDITION2_REVIEW_20261122.md",
                          "sha256": "9aafa1f219d0d226fc2cb172f97cb36923fa394edcd857ebd03a2019f053bc6c"},
 "sha256": "5432d313d7f9301cae5fd69f163b28fcd686a8ca815c737167abea7a83358144"}
```

(`5432d313…` is the approved-true addendum's content sha256; git blob `d48c7daf…`. My copy's PLAN sha256
`43deb82c…`, blob `68257fca…`.) The code under test is the pinned code: `r1/c3/audit.py` (`2ef055a8…`) and
`r1/c3/sweep2_batch.py` (`05db82fd…`) are byte-identical at `db7f344d` and `533b06ed`; the six files the
precondition-2 review names (`audit.py`, `sweep2_batch.py`, `dataset.py`, `release.py`, `analysis_guard.py`,
`release_checks.py`) have no diff between `db7f344d` and `533b06ed`.

**Negative controls (all fail closed, rc 1, in the same copy by rewriting `origin/main`):**

| Control (commit) | Rejected with |
|---|---|
| approved key `false` (`fa95a466`) | `ValueError: addendum key block does not read approved: true` |
| start row removed (`c1d28cbc`) | `ValueError: the start row R1-SWEEP2-B2-GO (one author row …) is not on origin/main` |
| wrong 64-hex table pin (`2ea489f1`) | `ValueError: the precondition-2 review on origin/main does not accept the four pinned sha256 values` |
| review without `Verdict: ACCEPTED` (`d6aed9a5`) | same review/pins ValueError |
| review missing one pin (`2dc91726`) | same review/pins ValueError |

So acceptance requires both the `approved: true` flip and the row, and the review presence/verdict/pins are
enforced, as the addendum claims. No push beyond `/tmp` and no write to the real repository was made.

## 2. Addendum content vs code and draft — PASS (minor compressions only)

- Key block: `approved: false` (branch) / `true` (simulation), `label: EVIDENCE`, `phase: c3_sweep2_b2`,
  `sweep2_run_id: s2ev-20261119-a`, `start_ruling: R1-SWEEP2-B2-GO`, four 64-hex pins,
  `precondition2_review: docs/r1/reviews/S2_AUDIT_PRECONDITION2_REVIEW_20261122.md`,
  `parent_authorization: docs/r1/authorizations/c3_sweep2_20261119.md (sha256 349e502b40b75a02b372cf495e78980145ede7c883f7868cc6228e9daa27e86a)`
  — every value matches the code's `want` dict (`approved`/`label`/`sweep2_run_id`/`start_ruling`), the draft's key
  block, and `sweep2_batch.AUTHORIZATION`; the parent-authorization sha256 is the sha256 of the published file.
- Counts: "**2,500 eligible, 2,512 duplicates, 0 no-ops; 1,064 unique configurations, 10,640 seed runs**" equals
  `precondition2/counts.log` and the precondition-2 review's independent partition (2,500+2,512 = 5,012 proposals;
  1,064 × 10 = 10,640; the code's `partition_population`/`planned_seed_runs` reproduce it).
- Projection/deadline: `10,640 / 4,660 × 23 min = 52.516 min ≈ 52.5 min`; `2.5 × T = 7,877.4 s ≈ 7,877 s`;
  `max(10,800, 7,877) = 10,800 s` — arithmetic correct; the sweep-1 basis 4,660 seed runs in 22 min 44 s is the
  published sweep-1 B.2 record (`counts.json`: 466 unique configurations; `START.json` 00:27:38Z → `PASS.json`
  00:50:22Z; 16 workers), so using 23 min is conservative.
- Host/workers/cores: "deepthought, CPUs only, in the e1-replayed batch venv; 16 workers, at least 10 of 40 cores
  free" matches `E1_HOST = 'deepthought'`, `evidence_resources`' workers ≤ 16 / workers < cpus, and the draft D1 A
  (40 cores is the sweep-1 START co-tenancy record). Scratch/output/Ceph texts match `evidence_resources` and
  `evidence_output_path` (50 GiB Ceph floor, dedicated `/tmp/r1_c3_audit_EVIDENCE_…`, new
  `results/r1/evidence/C3_audit_EVIDENCE_…`).
- Command: `--source sweep2`, `--table`, `--paper-root`, `--index`, `--out`, `--workers`, `--deadline`,
  `--code-commit`, `--code-review`, `--addendum`, `--scratch-root`, `--required-scratch-bytes`,
  `--ceph-reserve-files` all exist in the `evidence-run` parser; `PYTHONDONTWRITEBYTECODE=1`, python `-B`,
  `AR_HARNESS_ROOT` and no `env.sh` `PYTHONPATH` are exactly what `evidence_environment`/`evidence_paper_provenance`
  require. The filled `--deadline 10800`, `--required-scratch-bytes 17179869184`, `--ceph-reserve-files 2000` equal
  the sweep-1 B.2 operator values, so they are supported rather than invented.
- Pass rule / design: K = 10, seeds 7001–7005 label / 7006–7010 evaluation (`DEFAULT_SEEDS`, `split_seeds`),
  duplicates unlabelled, no-ops by rule (`evidence_blocks`), completion schema `r1.c3_audit_completion/4` with
  `source: sweep2`, binding the batch/table/plan/blocks/environment/authorization/addendum (`_completion`) — all match
  code. The "the audit rebuilds the table and refuses any difference" claim matches `_sweep2_plan` (batch
  `verify`, `_verify_replay`, `build.json`/table re-hash).
- Start row: the `R1-SWEEP2-B2-GO` row on `main` is one author row (`r1.c3.release.author_rows`), naming the run id,
  R1-SWEEP-HOST-HTC, R1-B2-DECOUPLE, B6 (a), B4 (a), B1 (a) — the same shape the code requires (§4).
- STOPs: present and fail-closed in code for guard, harness-equivalence, resources/co-tenancy, invalid/absent/
  non-finite/file-changing seed runs, deadline and interruption (`evidence_scratch` writes `STOP.json`); no use of
  7006–7010 outside the evaluation block is structural. Report/review carry the longer list from the draft; the
  addendum compresses it (MINOR 2 below).
- No claim in the Pins/Environment/Command sections conflicts with the code. The compression deviations from the
  draft are recorded as Findings MINOR 1–3; none changes the authorization's meaning or the audit's guards.

## 3. Pins vs actual artifacts (deepthought) — PASS

Re-hashed on deepthought (`ssh deepthought.etp.kit.edu`, read-only):

| Artifact | sha256 | Equals addendum/review pin |
|---|---|---|
| `/work/dwong/s2_audit_20261122/table/proposals.jsonl` | `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` | yes |
| `/work/dwong/s2_audit_20261122/table/configs.json` | `de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` | yes |
| `…/paper/results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/C3_sweep2_index_s2ev-20261119-a.json` | `b4697c496ca00659b8768afad238ae1bd20e1335597dd6a69cfdc1a23b7460b4` | yes |
| `…/C3_sweep2_batch_s2ev-20261119-a/EXTRACT.json` | `82c7605291cc07d5d06dc610c6f9a34e6e8d417e62cadb7de7ca59d7b103a4da` | yes |

`table/build.json` is `bbb2a95cef1edfb1e3767eb66b841c54626235b1e3b719529e4b53f37d3dda92`, byte-identical to the
committed copy; the deepthought checkout is detached at `db7f344d6ac372737444db5ab036d370543ea65f` with only the
untracked batch output `results/r1/evidence/C3_sweep2_batch_s2ev-20261119-a/`, as the report states. I ran
`_sweep2_pins_match` at `db7f344d` on deepthought in the batch venv (Python 3.13.15) with these four values and the
actual index/table/extract: it returns `PINS_MATCH_OK`; with one pin altered it raises
`STOP: the sweep-2 batch or table differs from the addendum's pins`. The checked-in `precondition2/` copies of the
index and `EXTRACT.json` hash equal to the host files. The `precondition2_review` file contains the exact line
`Verdict: ACCEPTED` and all four full pins (the code's `b2_addendum` requirement), which the §1 acceptance
exercised.

## 4. D1 start row — PASS

I reconstructed the proposed row from the draft's D1 block (continuation lines joined with one space, `  > ` markers
removed, `<date>` → `20261122`): 903 characters, byte-identical to the row in the pre-existing simulation commit
(see Finding 5) and to the row I inserted. On the simulated published `main`, `r1.c3.release.author_rows(PLAN)`
returns **exactly one** `R1-SWEEP2-B2-GO` row (line 1383); it sits in PLAN §10, inside the dated author table
`### 22 November 2026 — sweep-2 audit decisions, G.4 pilot, G.1b second note and cross-host check, P.4 wheel rule
(author)`, immediately after `R1-SWEEP2-B2-DECISIONS`. It names `s2ev-20261119-a`, R1-SWEEP-HOST-HTC,
R1-B2-DECOUPLE, B6 (a), B4 (a), B1 (a), harness `6adf3859` equal to `a3fedbbd` (checked at run time), K = 10, and
the addendum file date `c3_sweep2_b2_addendum_20261122.md`. On the reviewed base there are **zero** such rows, so
publication must add it exactly as proposed; the published `R1-SWEEP2-B2-DECISIONS` row already authorizes that
("the start row R1-SWEEP2-B2-GO, with the text proposed under D1, is committed together with the published
addendum"). Semantics and all code-required tokens pass; punctuation/placeholder differences are none (identical
text apart from the filled date).

## 5. Independence and evidence

- **No label/evaluation file read:** the branch diff over `9c2979a2` contains no path matching label/evaluation/
  sealed data (8 files, listed above); the extraction/`counts`/`verify` paths are ENGINEERING_ONLY and the
  precondition-2 report states no label was read. The precondition-2 review itself discloses, correctly and
  harmlessly, that a `grep` over the historical sweep-1 B.2 report directory incidentally matched two lines of the
  already-published sweep-1 `label_block.jsonl` (the literal `4660` inside a `se_label` value); no sweep-2 label
  exists or was opened, and none was used. The addendum's "no label or evaluation file was read to fill this
  addendum" therefore holds (the fill used the pins/counts from the engineering output), with that disclosure on
  record.
- **Sealed tree not copied:** the sealed tree was read on deepthought (report: 594 files, `sealed_rederivation:
  equal`); the 7.5 MB table stays at `/work/dwong/s2_audit_20261122/table` and is bound by sha256. The branch carries
  batch/table metadata (index, `EXTRACT.json` hashes/paths, `build.json`) only — no sealed chunk, ledger or label
  file.
- **Commands/logs:** the four documented commands and their environment are recorded in
  `PRECONDITION2_20261122.md`; `extract.log`, `build.log`, `counts.log`, `verify.log` exist on disk and all seven
  `precondition2/SHA256SUMS` entries verify in the worktree. **But they are not committed** — see BLOCKER 1.
- **Review path/sha:** the addendum's `precondition2_review` path exists at the reviewed commit; the review's
  sha256 is `9aafa1f2…`, ends with `Code-Commit: db7f344d…` (line 162) and `Verdict: ACCEPTED` (line 163), and the
  accepted call in §1 records the same review sha.
- **Addendum sha on branch:** blob `8ed780f7…`, sha256 `0c017864…` at `533b06ed`; `approved: false` kept there
  (`git show 533b06ed:…` line 13) and in the worktree, which is byte-identical to `533b06ed`
  (`git diff 533b06ed` empty). Note: the *local branch ref* is no longer `533b06ed` (Finding 5).

## Findings

**BLOCKER 1 — the four precondition-2 logs are gitignored and absent from the commit; the evidence bundle would
publish broken.** `precondition2/extract.log`, `build.log`, `counts.log`, `verify.log` are matched by `.gitignore:3`
(`*.log`), untracked/ignored (`git ls-files` lists only the other four files of the directory; `git status
--ignored` shows `!!` on all four). They are real and complete on disk, and `precondition2/SHA256SUMS` lists them
with their sha256, but they are not in `533b06ed`: in a fresh checkout `shasum -a 256 -c precondition2/SHA256SUMS`
reports `build.log/build.log … FAILED open or read` ×4 (`WARNING: 4 listed files could not be read`, rc 1), whereas
the worktree passes 7/7. `PRECONDITION2_20261122.md` says "full logs in this directory", the precondition-2 review
compares its stdout to `verify.log` and reports "all 7 entries OK", and the data commit message promises "four pins
and logs". Publishing the branch as it stands therefore publishes a `SHA256SUMS` that fails and a review whose cited
logs do not exist on `main`. **Fix:** force-add the four logs byte-identically (`git add -f
docs/r1/reports/s2_audit_20261121/precondition2/{extract,build,counts,verify}.log`; precedent in this repo:
`7f1e09aa` "add raw logs … (gitignore force-add)", `42f13cc07` co-tenancy log, and the e1 `logs/` directory), commit
before publication and verify a fresh checkout passes 7/7. This adds no new content: the addendum's, review's and
pins' bytes are unaffected, so §1–§4 remain valid and only the fresh-checkout `SHA256SUMS` check needs re-running.

**BLOCKER 2 (workspace, not a defect of the reviewed files) — the local branch ref has been advanced past the
reviewed commit by an external simulation, and a simulation tree shares this worktree's git directory.**
`s2-audit-addendum-20261122` locally points at `9c772420` ("sim published main with addendum approved true + start
row"), while `origin/s2-audit-addendum-20261122` is `533b06ed`; the worktree's tracked files were restored to
`533b06ed` (`git diff 533b06ed` empty) but the ref and reflog retain the simulation commit, and
`/tmp/s2_sim_remote.git` plus `/tmp/s2_sim_repo` exist (`/tmp/s2_sim_repo/.git` is a *file* pointing at
`.git/worktrees/s2-audit-addendum-20261122`, i.e. it shares this worktree's index/HEAD — a git command there can
mutate the real repository). `9c772420` must never be pushed to the publication remote: it contains
`approved: true` and the start row before the author's signature, which would bypass the review/approval gate.
**Fix:** before publication, reset the local branch to `533b06ed` (`git reset --hard 533b06ed`) or publish from
`origin/s2-audit-addendum-20261122`/a fresh clone, and remove `/tmp/s2_sim_remote.git` and `/tmp/s2_sim_repo`
(`rm -rf`). My §1 test did not use these artifacts; it built an independent copy from `git archive 533b06ed`, and
that copy reproduces exactly the same addendum/PLAN bytes (`d48c7daf…` / `68257fca…` blobs), which cross-checks
the simulation fixture's content but not its placement on the branch.

**MINOR 1 — the signature flip should also update the draft front matter.** The H1 (line 1) reads "…: B.2
fresh-seed audits of sweep 2 (approved: false)" and line 3 reads "**Draft for the author's signature — it authorizes
nothing until `approved: true`.**" When the coordinating chat flips the key line to `approved: true`, these should be
updated too, or the published signed document contradicts its own key block. Precedent: the sweep-2 authorization
`c3_sweep2_20261119.md` was approved by editing title and banner (`344e387a`), and the signed sweep-1 B.2 addendum
(`c3_b2_addendum_20261117.md`) carries no such draft framing. This is a documentation edit at signature, not a code
requirement (the guard ignores these lines).

**MINOR 2 — the STOP summary is a compression of the draft's list.** The draft's STOP list explicitly includes
"the index, `EXTRACT.json`, `proposals.jsonl` or `configs.json` sha256, or the counts, at audit time differ from this
addendum's values", "`docs/r1/PLAN.md` changes on `main` while the audit runs", and the "projection above 2 h is
reported to the author" rule. The addendum compresses these into "Any guard failure, …". The sha/counts case is
enforced by `_sweep2_pins_match` at run start (and again at consumption); the PLAN-drift and 2 h cases are operator
protocol, not code guards. Recommend restoring those two bullets in the signed text — cheap and it keeps the
authorization faithful to D5/D1 A.

**MINOR 3 — two operator prerequisites are not restated in the addendum.** The command shows `--code-commit
db7f344d…` with an ellipsis; `evidence_paper_provenance` rejects any value that is not exactly 40 hex characters
(`len(code_commit) != 40`), so the operator must paste the full `db7f344d6ac372737444db5ab036d370543ea65f` from the
Pins table. Also draft precondition 3 — fetch `a3fedbbd` into the batch harness repository — is still outstanding
(the precondition-2 review records that it is not yet fetched); without it the run fails closed with
`NOT CHECKABLE: harness commit a3fedbbd… is not present`. Neither is a false claim in the addendum, but a signed
addendum is a better place to record both than run prose.

**MINOR 4 — "at least 10 of 40 cores free" is operator-enforced, not a code guard.** `evidence_resources` enforces
workers ≤ 16 and workers < CPU count and `monitor_evidence_resources` watches scratch/Ceph during the run; it does
not sample free cores. The addendum's "a breach during the run is a STOP" is therefore a co-tenancy protocol
(sweep-1 `cotenancy.log` practice), which is fine as an instruction but should not be read as a code check.

**Observation — the "exactly one author row" behavior is the only row-level guard.** The code uses
`author_rows(PLAN)` and requires exactly one `R1-SWEEP2-B2-GO` row in a dated §10 table; my simulated PLAN and the
proposed text both satisfy it (`author_rows` returns one). No second row or table-form ambiguity was found in the
base `PLAN.md` or the simulation.

## Verdict

**VERDICT: NOT ACCEPTED** for publication as the branch stands.

- The filled addendum's substance is correct and ready: **code accepts `approved: true` + the exact D1 row in an
  independent simulated published `main`; all five negative controls fail closed; the four pins equal the actual
  deepthought artifacts and `_sweep2_pins_match` accepts them; counts, projection, deadline, host/workers/resources,
  command, pass rule, STOPs and independence all check out; `approved: false` is kept on the reviewed commit.**
- Publication blockers: (1) the four precondition-2 logs are gitignored and absent from the commit, so the published
  `SHA256SUMS` fails 4/7 and the report/review cite missing files — force-add them; (2) the local branch ref is the
  external simulation commit `9c772420` and must be reset to `533b06ed` (and `/tmp/s2_sim_*` removed) so the
  reviewed `approved: false` state is what gets published.
- After those two fixes (log bytes unchanged; no other file changed), the addendum **is publishable with
  `approved: true` and the `R1-SWEEP2-B2-GO` row**, after MINOR 1's front-matter edit; no content re-review is
  needed for the log fix, but the publication commit and a fresh-checkout `SHA256SUMS` 7/7 check should be
  re-confirmed.

## What I did not do

Read-only in the real repository and on deepthought (only sha256/git-read/python hash calls; no push, no commit, no
branch/ref change, no `extract`/`build-sweep`/`counts` write, no table rebuild). My throwaway test copy and its bare
`origin` live under `/tmp/s2_b2_addendum_review_20261122/`. I did not use the pre-existing `/tmp/s2_sim_*` material
except to cross-check bytes, and I did not touch it. No label or evaluation file was opened.

---

# Round 2 — re-confirm after publication fixes (`264896bb`) — **VERDICT: ACCEPTED**

Re-confirm target: branch tip **`264896bb`** (pushed; remote `refs/heads/s2-audit-addendum-20261122` = `264896bb`,
parent `533b06ed`), base published `main` **`9c2979a2`** (GitHub `origin` main = `9c2979a2`). Workspace restored: the
`origin` URL is back to `https://github.com/dowlingwong/Agent_paper_B.git`, local `origin/main` = `9c2979a2`,
`/tmp/s2_sim_repo` and `/tmp/s2_sim_remote.git` are absent, and `9c772420` is reachable from no branch or tag
(`git branch -a --contains 9c772420` empty). The fix commit changes exactly 6 files: the addendum (3 edits), the four
force-added logs, and my round-1 review committed verbatim (sha256 `9bf8ae04…`, 266 lines). The addendum remains
`approved: false` (line 13) and the branch PLAN has **0** `R1-SWEEP2-B2-GO` rows, so publication still adds the row.

## Blocker 1 (logs) — CLEARED

`git ls-tree 264896bb` now lists `build.log`, `counts.log`, `extract.log`, `verify.log` in
`docs/r1/reports/s2_audit_20261121/precondition2/`. A fresh checkout of the commit (`git archive 264896bb | tar -x`)
verifies `shasum -a 256 -c precondition2/SHA256SUMS` **7/7 OK, rc 0**. The four log sha256s equal the values already
listed in `SHA256SUMS` (`build.log` `db1f4a80…`, `counts.log` `b4806c1e…`, `extract.log` `1b5c188f…`, `verify.log`
`03602d10…`); no other `precondition2/` file changed. The published evidence bundle no longer has dangling files or a
failing checksum.

## Blocker 2 (workspace) — CLEARED

The branch was reset to `533b06ed` and the fix commit `264896bb` applied on top; the remote branch is `264896bb`; no
simulation commit was pushed (`9c772420` is unreachable from refs); the `/tmp/s2_sim_*` trees are gone; the shared
repo `origin` URL is back to GitHub, and `origin/main` is back at `9c2979a2` (reflog: forced-update
`9c772420` → `9c2979a2`). Nothing pre-signature can be published by accident from the branch.

## Re-acceptance — PASS

Independent copy built from `git archive 264896bb` (base commit `11c1e9cc`), key line flipped to `approved: true`, D1
row re-inserted from the draft (903 characters; `author_rows` → exactly one `R1-SWEEP2-B2-GO` author row), local bare
`origin` `main` = `ac092ce8…`. `r1.c3.audit.b2_addendum(root, 'docs/r1/authorizations/c3_sweep2_b2_addendum_
20261122.md', 'db7f344d6ac372737444db5ab036d370543ea65f', 'sweep2')` returns **ACCEPT** (rc 0): approved-true addendum
sha256 **`93a754893d38c22646c9a93c4d6189043470886bf5af0a798f57e7337b49a015`** (differs from round 1 only because of the
three signature/precondition edits; the key block and pins are unchanged), the same four pin values, and
`precondition2_review` sha256 `9aafa1f2…` (review bytes unchanged). All five negative controls again fail closed
(rc 1: approved false, missing start row, wrong 64-hex pin, review without `Verdict: ACCEPTED`, review missing one
pin). `_sweep2_pins_match` need not be re-run: the four pin values in the addendum are byte-identical to round 1,
which were verified against the live deepthought artifacts (`379b17ca…`, `de6d63b5…`, `b4697c49…`, `82c76052…`), and
the review file is unchanged.

## Minor edits — three applied, two claimed but absent

`(a)` **applied**: the signature note is added — "On signature the coordinating chat flips the key to `approved:
true` and updates this draft heading/prose; the reviewed facts and pins do not change" (covers the round-1
front-matter edit). `(c)` **applied**: the command now carries the full 40-hex
`--code-commit db7f344d6ac372737444db5ab036d370543ea65f`. `(d)` **applied**: precondition 3 (fetch `a3fedbbd…` into the
batch harness repository) is restored as its own paragraph.

**`(b)` and `(e)` are NOT in `264896bb`.** The only addendum changes in the fix commit are the three above: the
**STOPs** section and the co-tenancy bullet are byte-for-byte the round-1 text, and the file contains no `cotenancy`
mention. The commit message's "explicit STOP bullets" and "co-tenancy protocol wording" therefore overstate what was
committed. This is not a publication blocker — (b) and (e) were MINOR recommendations in round 1, the retained STOP
summary still names every fail-closed guard ("Any guard failure, harness-equivalence difference, resource/co-tenancy
breach, failed/missing/non-finite or file-changing seed run, deadline, interruption, or use of 7006–7010 outside the
evaluation block"), the co-tenancy rule remains the operator protocol of the draft/sweep-1 record, and no
authorization semantics or pins change. Recommended: either push the two small edits (and re-confirm this diff), or
record explicitly that the compressed wording stands.

## Round-2 verdict

**VERDICT: ACCEPTED — the filled addendum is publishable with `approved: true` and the `R1-SWEEP2-B2-GO` row on
`main`.** Conditions: (i) the signing step updates the heading/prose exactly as the new signature note says;
(ii) the (b)/(e) discrepancy is resolved (add the two edits or explicitly accept the current text); (iii) publication
starts from `264896bb` + the row and never from the unreachable simulation commit. No blockers remain: both round-1
blockers are cleared, the addendum still parses and is accepted by the code with `approved: true` + the D1 row, all
negative controls fail closed, and the four pins and counts are unchanged from the values verified against the live
deepthought artifacts. The committed review file is my round-1 review verbatim; this Round 2 section is appended
uncommitted in the worktree. Read-only otherwise: no real-repo/git/deepthought writes, and no label or evaluation file
was read.

---

# Round 3 (final) — minor (b)/(e) fix at `7fefb8b1` — **VERDICT: ACCEPTED / PUBLISHABLE**

Confirm target: branch tip **`7fefb8b1`** (parent `264896bb`; pushed — GitHub `refs/heads/s2-audit-addendum-
20261122` = `7fefb8b1`, `main` = `9c2979a2`). Diff `264896bb..7fefb8b1` = the addendum (7 insertions / 4 deletions)
plus my Round-2 section committed to this review file (+76 lines, sha256 `89c46a99…`); no other path changed. The
addendum edits are exactly the two claimed ones: (e) the host bullet now names the 16-workers/≥10-free-cores rule
"the operator protocol recorded in `cotenancy.log`; a breach during the run is a STOP", and (b) the compressed STOP
paragraph is replaced by explicit bullets (pin/count/table drift; start-row/authority drift; precondition-2 or code
review missing; D8/start-row guards; harness-equivalence/untracked-harness/current-environment difference;
resource/co-tenancy breach; seed-run/deadline/interruption/evaluation-seed misuse). Key block, pins and counts are
byte-identical to round 2; the addendum is still `approved: false` (line 13) and PLAN still has **0**
`R1-SWEEP2-B2-GO` rows. A fresh checkout of `7fefb8b1` verifies `precondition2/SHA256SUMS` **7/7 OK**.

Re-acceptance on the new content: independent copy from `git archive 7fefb8b1` (base commit `9397519d`), key line
flipped to `approved: true`, D1 row re-inserted from the draft (903 characters; `author_rows` = exactly one), local
bare origin `main` = `f91b16e3…`: `b2_addendum(…, 'db7f344d…', 'sweep2')` **ACCEPT** — approved-true addendum sha256
**`9282bd1f9f14730cbb4797c4562b7da7391647af65b33df4ddc709bf10603c67`**, the same four pins and review sha
`9aafa1f2…`. As a control, the unmodified branch content (approved: false) is refused
(`ValueError: addendum key block does not read approved: true`), so the gate still separates the unsigned branch from
the publication state.

**Round-3 verdict: `7fefb8b1` is publishable with `approved: true` and the `R1-SWEEP2-B2-GO` row on `main`; no
blockers remain.** At signature the coordinating chat must (i) flip the key to `approved: true` and update the draft
heading/prose as the addendum's signature note says, and (ii) add the D1 row exactly as proposed; publication must
start from `7fefb8b1` + the row. Pins and counts need no re-derivation — they are unchanged from the values verified
against the live deepthought artifacts. This Round 3 section is appended uncommitted in the worktree; read-only
otherwise (no real-repo/git/deepthought writes, no label or evaluation file read).
