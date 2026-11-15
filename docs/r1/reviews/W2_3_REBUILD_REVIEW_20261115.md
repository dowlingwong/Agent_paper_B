# Independent review — W2 v3 Track P data rebuild unit (branch `w2-3-rebuild-unit-20261115` @ `6fa29c4f`)

**Reviewer role:** fresh, independent, read-only reviewer. Not the author of the unit, not the executing agent.
I read the branch, the reviewed code at `d8aa9561`, the authority rows and the W2-3 evidence; I ran nothing on a
host, wrote nothing except this review, and made no git commit. The unit is reviewed **before execution**, per the
author's instruction.

**Date/time of review:** 15 November 2026, 23:05–23:55 CET (Europe/Berlin).

**Reviewed unit:** branch `w2-3-rebuild-unit-20261115` at pinned commit **`6fa29c4f`** (pushed; based on
`w2-3-check-20261115` @ `03d742cf`, based on the reviewed `mac-w2-v3-rebuild-20261115` @ `d8aa9561`); the commit
adds exactly two files (`git show --stat`). Worktree
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/w2-3-rebuild-unit-20261115`.

**Basis / authority:** author rows `R1-W2-3-STOP` and `R1-B2-REPAIR-SCOPE-ACK` (`author-ack-w23-20261115` @
`b0c8a48d`, PLAN §10); `reports/W2_V3_REBUILD_20261115.md` §2 (rebuild every Track P feature table and prompt set,
write `FEATURIZER_VERSION` and the prompt version into every table's manifest, do not mix v1/v2 prompts, disclose
both versions and the budget-line change; the synthetic exam `trackp_e0/v1` keeps the v1 budget line — W2-4 open);
the W2-3 PASS check on `w2-3-check-20261115` @ `03d742cf` (JSON SHA `b11217d0…`: status PASS, 288/288 ledgers,
exactly 20 worker runs, 0 differing, trial budget 40); the reviewed code at `d8aa9561` (the pre-existing reviewed
`build-sweep` tool, STATUS.md A.4) and the prior accepted check-unit review
`reviews/W2_V3_REBUILD_REVIEW_20261115.md`.

---

## 1. Files and pins (verified)

| Item | Value |
|---|---|
| `w2_3_rebuild_20261115/run_rebuild.sh` | 102 lines, SHA-256 `a0601bcdf99e0d0bf3234892c654edc8560a08b2bd6d3689800399149d12bb91` |
| `docs/r1/reports/w2_3_rebuild_20261115/PLAN.md` | 57 lines, SHA-256 `e0ea6290620d02ff75e2c8c8061c51a1b62dd51222b591da6ad892f1e2a9eb13` |
| Code commit (verify target) | `d8aa956193ba1b24ae0b568a724b841beaa1651e` (reviewed branch head) |
| Sweep-1 index pin | `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, SHA-256 `812468e2…` = the `SWEEP1_INDEX_SHA` constant in `r1/c3/analysis_guard.py` (the `R1-DT-PIN-SWEEP1` file) |
| W2-3 PASS evidence | repo `docs/r1/reports/w2_3_check_20261115/w2_3_check_20261115.json`, SHA-256 `b11217d0…` (matches the unit's `EVIDENCE_SHA`); fields `status=PASS, ledgers=288, runs_total=20, ledgers_differing=0, trial_budget=40` |
| R1-SWEEP1-CLASSIFY sidecar (not used by the unit — see R1) | `results/r1/evidence/C3_sweep_classification_20261028.json`, SHA-256 `bb6d891c…` (tracked) |

---

## 2. Checks performed

### (a) Input pins, and the only data-producing step is the reviewed `build-sweep`

Verified in the script and against the reviewed code:
- **Checkout:** `[ -d "$CHECKOUT/.git" ]`, `git rev-parse HEAD == d8aa9561…`, `git status --porcelain` empty, all
  before anything runs — correct.
- **Index:** exists + SHA-256 == `812468e2…`; the value is the code's own `SWEEP1_INDEX_SHA`, so the unit pins the
  same file the reviewed code treats as the sweep-1 authority. `--paper-root` is passed to the build; `--index` is
  the pinned file. The code's `build_from_sweep` re-verifies the index/pin and calls `refuse_sealed` on the sweep,
  output, paper root and (if given) summary/classification, and refuses `r1_sealed` paths lexically and via
  `resolve()` — the unit's own extra `readlink -f` guard (L31) is redundant but harmless (see NIT 3).
- **Evidence:** exists, non-empty, SHA-256 == `b11217d0…`; the same JSON is the repo evidence (the unit points at
  a `/work` copy; the SHA pin covers content — NIT 2).
- **Single data-producing step:** the only command that writes table data is
  `python3 -m r1.c3.dataset build-sweep --index … --paper-root … --out …`; `_write_table` writes exactly
  `proposals.jsonl`, `configs.json`, `build.json` under `--out` (and `table_sha256` additionally when the head
  label is `EVIDENCE` — see R1); the other python invocations only read two version constants / write the manifest
  and verify it; `sha256sum`/`grep` write nothing. The build path opens the sweep ledgers and the paper root
  read-only (with `refuse_sealed` checks), and does not touch the v1 tables, `/ceph` sources or the checkout's
  tracked files. ✓ (with R2/R3 below).

### (b) New directory / never-overwrite / read-only behaviour

- `umask 077`; `OUT = …/w2_3_rebuild_20261115/tables/c3_features_v3_<UTC>`; `[ ! -e "$OUT" ] || stop` (never
  overwrite); `mkdir -m 700 "$OUT"` (0700); `mkdir -p "$BASE/tables"` only for the structural parent. On a STOP no
  `rm`/`mv` occurs, so a partial output directory survives; the build's stdout/stderr are redirected **into** the
  partial directory, which is exactly what a post-mortem needs. The final `REBUILD_OK` is written under
  `set -C` (noclobber) → exclusive success marker. v1 tables are never referenced as an output. ✓
- **Read-only caveat (R3):** the unit does **not** set `PYTHONDONTWRITEBYTECODE=1` / `python3 -B`, and the
  build/version commands run with `PYTHONPATH=.` from the checkout. Python will write `__pycache__` directories
  into the checkout (`r1/c3/…`). `__pycache__/` is in `.gitignore`, so `git status` stays clean, but this is a
  filesystem write **outside the new output directory**, contradicting the PLAN's "no data is written outside the
  new table directory" and the unit's read-only spirit. One environment variable (or `-B` on every python call)
  fixes it; alternatively run from a pristine copy.
- The unit writes no logs outside `OUT`; the STOP reason goes to stderr (terminal) and the partial dir holds the
  build logs. ✓

### (c) Manifest / version / mixing guards

What is right:
- `FEATURIZER_VERSION` is read from `r1.c3.features` and enforced `== c3_features/v3`; `PROMPT_VERSION` is read
  from `r1.c3.train.types` and enforced `== trackp_prompt/v2` — i.e. the manifest's versions are the code's, not
  free text. ✓
- The code-level mixing guard refuses unless exactly one distinct `trackp_prompt/v*` appears in
  `r1/c3/train/types.py` + `r1/c3/train/serialize.py`; the post-build scan refuses if any generated file under
  `OUT` contains the literal `trackp_prompt/v1`. ✓ for the table itself.
- The manifest records: schema, unit, `code_commit`, `featurizer_version`, `prompt_version`, a mixing statement, the
  sweep-index path+sha, the W2-3 evidence path+sha+status+ledgers, the table label/`n_proposals`/`n_configs`/
  `replay_checks_total`/`sweep_index`/`sources` from `build.json`, the file SHA-256s, the v1 policy and the
  disclosure. `SHA256SUMS` covers the three table files + the manifest; `REBUILD_OK` carries the versions and the
  output path. The manifest verify checks the versions, the counts against `build.json`, the file set, and that
  `build.json`'s recorded sweep-index SHA equals the input SHA (the code records `sweep_index` in `build.json`
  exactly this way). ✓

What is wrong / missing (see findings): the manifest's `paper_root` field is wrong (R2); the mixing statement
overclaims and the required disclosure is incomplete (R4); and the table's `label`/classification is undecided
and will be the runner-defect label (R1).

### (d) STOP / no-retry / no-deletion handling

The script is a straight-line `set -u; set -o pipefail` (no `set -e`) with explicit `|| stop` on the critical
checks (checkout, pins, evidence, output existence, mkdir, version reads, build rc, table files, manifest, manifest
verify) and the `stop()` exits 2 with the reason. There are **no retries** and **no deletions**; the partial output
directory is preserved; the success marker is exclusive. This matches the author's "STOP 时保留现场、报告，不重试".
✓ with NITs: `sha256sum … > SHA256SUMS` (L97) has no `|| stop` and is not self-verified (`sha256sum -c` before
`REBUILD_OK` would close the loop); the manifest-writer python step (L56) relies on the later `[ -s "$MANIFEST" ]`
check; the no-mixing `grep` scans `build.stdout`/`build.stderr` too, so a build log line containing the token
would STOP a correct build (restrict the scan to the table files or exclude the logs); the `PCOUNT` guard only
scans two files (the code's intentional `trackp_prompt/v1` mentions in `exam_synthetic.py` and the test golden JSON
are outside it — correct for this build, but the manifest's wording must say so, R4).

### (e) Additions recommended before running

Beyond R1–R4: (i) **row-count cross-check** — the W2-3 evidence gives `ledgers=288, runs_total=20`; the manifest
already records `replay_checks_total`, but the verify only compares the manifest to `build.json` (tautological) and
`n_proposals > 0`. Assert/record `replay_checks_total == 288*20 = 5760` (and the evidence's `ledgers`/`runs_total`)
in the manifest verify — a cheap, strong guard that the table actually rebuilt the whole sweep; also cross-check
`n_configs` against the index/manifest config count if derivable. (ii) **environment preflight/record** — the build
imports `numpy` (and `r1.headroom.e1b_collect`), so record `python3 --version` and `numpy.__version__` in the
manifest (and check them before the build); the rest of the code is stdlib. (iii) **disk-space preflight** (`df`
on `$BASE` with a threshold) since the table JSONL/config sizes are not recorded. (iv) record the **exact build
command** in the manifest (the "single data-producing step" should be reproducible from the evidence). (v) run with
`-B`/`PYTHONDONTWRITEBYTECODE=1` (R3) and, if desired, from a pristine copy of the checkout.

---

## 3. Findings

### BLOCKING

None.

### MAJOR

**R1 — the rebuilt table's `label`/classification is undecided and defaults to the known runner-defect string.**
The unit runs the reviewed `build-sweep` **without** `--classification`, so `build_from_sweep` takes
`decision = None`, the head label becomes `index.get("label")`, and that is the index's `PILOT`/`ENGINEERING_ONLY`
string that the author's `R1-SWEEP1-CLASSIFY` row explicitly calls a **runner defect**, not a request to rerun
B.1; the classification sidecar (`results/r1/evidence/C3_sweep_classification_20261028.json`, SHA `bb6d891c…`,
tracked) is the file that binds the index to the sweep-1 **EVIDENCE** batch. Consequences: (i) the v3 table's
manifest would record the defect label as `table.label`; (ii) the EVIDENCE-only `table_sha256` record in
`build.json` is not produced; (iii) the classification path+sha is absent from the manifest — exactly the
provenance the author's row asks to bind. *Fix/decision before running:* pass
`--classification "$PAPER_ROOT/results/r1/evidence/C3_sweep_classification_20261028.json"` (pin its SHA-256
`bb6d891c…` in the script and record it in the manifest), **or** record in the manifest/PLAN that the defect label
is intended and why (author decision). Note the mechanical constraint: with `--classification` the reviewed code
does `out.mkdir(parents=True, exist_ok=False)`, so the unit's pre-created `OUT` (and its stdout/stderr redirection
into `OUT`) makes `build_from_sweep` raise `FileExistsError`; the unit must therefore create only the parent and
redirect the logs outside `OUT` (or otherwise adapt) in classification mode — this must be sorted out and
re-reviewed before running.

**R2 — the manifest's `paper_root` field is the output's parent directory, not the input paper root.**
The manifest-writer gets `$OUT`, `$MANIFEST`, the code commit, the index, the evidence and the version strings, but
**not** `$PAPER_ROOT`; it writes `"paper_root": str(pathlib.Path(out).parent)` — i.e. `…/w2_3_rebuild_20261115/tables`,
not `/ceph/…/agent_paper_B`. The evidence would record a wrong input root (the sweep index lives under
`/ceph/…/agent_paper_B/results/r1/pilot`, and `build.json`'s `sweep_index.path` is the true index path, so the
error is detectable but still wrong). *Fix:* pass `$PAPER_ROOT` into the python (one argv) and record it; keep the
output's parent under a separate key if wanted.

### MINOR

**R3 — Python bytecode writes into the checkout.** No `-B`/`PYTHONDONTWRITEBYTECODE=1` on the build/version
commands; `__pycache__` lands in the checkout (gitignored, so `git status` stays clean, but the "no writes outside
the new directory" claim is false). Fix with one env var / `-B` on every python invocation (and, if wanted, run
from a pristine copy).
**R4 — the mixing statement overclaims and the report-§2-item-3 disclosure is incomplete.** The manifest says "the
reviewed code defines exactly one prompt version (trackp_prompt/v2)"; the reviewed code also contains
`trackp_prompt/v1` in `r1/c3/train/exam_synthetic.py` (by design: the synthetic exam keeps the v1 budget line,
W2-4 open) and in the test golden JSON. The report §2 item 3 asks to disclose both versions **and the budget-line
change**, and the synthetic exam's retained v1 line. Reword the mixing statement to scope it to the Track P table
build path, add the exam/W2-4 disclosure and the budget-line-change sentence; optionally broaden the code-level
guard to the whole `r1/c3` tree with an explicit allowlist (exam_synthetic.py, tests/data) so future edits cannot
smuggle a v1 line into the Track P path.
**R5 — no row-count cross-check against the W2-3 evidence.** Add the `replay_checks_total == ledgers ×
runs_total` (= 288 × 20 = 5760) assertion and record `ledgers`/`runs_total`/`trial_budget` in the manifest (the
current verify is manifest-vs-`build.json` only).
**R6 — no environment/disk preflight.** The build imports `numpy`; the unit records no `python3`/`numpy` version
and no disk-space check. Record both (and the exact command) in the manifest before running.

### NIT

1. `sha256sum … > SHA256SUMS` should be `|| stop` and followed by `sha256sum -c SHA256SUMS` before `REBUILD_OK`.
2. The `EVIDENCE_JSON` is a `/work` copy; record the repo evidence path/SHA too (the SHA pin already binds it).
3. The unit's own `r1_sealed` case check uses `readlink -f` on a not-yet-existing path (empty output, no match);
   harmless because the reviewed code's `refuse_sealed` covers the inputs — keep or simplify.
4. The no-mixing post-build `grep` scans `build.stdout`/`build.stderr`; restrict to the table files/manifest, or
   exclude the logs (a log mentioning the token would false-STOP).
5. The W2-3 evidence JSON's internal `stop_rule` string still says "proposed (adoption is a separate author
   decision)" although the author adopted it (`b0c8a48d`); the manifest could note the adopted row.
6. The `PCOUNT` guard's two-file scope should be stated in the PLAN/manifest (see R4).

---

## 4. Verdict and run conditions

The unit may **not** run on deepthought as written: R1 and R2 must be fixed and re-checked first (both are small code changes in the unit, no data impact, no need to re-review the reviewed
`build-sweep`). R3 and R4 should be fixed in the same pass (read-only claim and the author-required disclosure);
R5/R6 are cheap strengthenings that I recommend adding now but would not block on.

The rest of the unit is sound and well pinned: the code commit (`d8aa9561…`), the sweep-1 index
(`812468e2…` = the code's `SWEEP1_INDEX_SHA`), the W2-3 PASS evidence (`b11217d0…`, 288/288 ledgers × 20 runs,
0 differing), the single data-producing `build-sweep` path (writes only the three table files under the new
directory; the code's `refuse_sealed` on the sweep/paper root/classification), the new 0700 versioned directory
with never-overwrite, no retry, no deletion and a preserved partial output, the code-derived
`c3_features/v3` + `trackp_prompt/v2` versions, the manifest/SHA256SUMS/exclusive-REBUILD_OK evidence, and the
no-v1-token post-build scan. Once R1 (classification/label decision and the associated directory-creation
constraint) and R2 (paper root in the manifest) are fixed and R3/R4 are folded in, a quick re-check is enough and
the unit may then run on deepthought.

**Review limits:** read-only; no host access and no execution (the `/ceph` index and paper root are not reachable
from here, so the pins are checked against the repo evidence and the reviewed code, not by opening the live
files); no git commit; the only file written is this review.

VERDICT: NOT ACCEPTED

---

## Round 2 delta re-check (branch @ `c83d6620`; 16 Nov 2026, 00:15 CET)

**Scope.** Re-check of round 2 at HEAD `c83d6620` (worktree clean; my round-1 review is committed there):
`run_rebuild.sh` SHA-256 `f9a01dd2a46b6a3eaa6cf2a186c095dfcc306ad3f1b6a144ad281d939ff16aee` (139 lines),
PLAN.md `3491b5fcbec991562cb1550819799b2ad616b0517b0674f60d67a2928769934a` (73 lines). Read-only; no host access;
nothing executed.

**Verified fixed:** R2 (`paper_root` is an explicit argv; `output_parent` a separate key) ✓; R3
(`PYTHONDONTWRITEBYTECODE=1` exported and `python3 -B` on every invocation) ✓; R4 (mixing statement scoped to the
Track P table build path, `budget_line_change` disclosure with the W2-1 v1→v2 line, the synthetic exam's retained
v1 line (W2-4) disclosed, and the post-build v1-token scan restricted to the three table files) ✓; R5
(`replay_checks_total == 288*20 == 5760` asserted; the evidence JSON's status/ledgers/runs_total/
ledgers_differing recorded) ✓; R6 (python/numpy versions, a `df -Pk` free-space preflight ≥2 GiB, and the exact
build command recorded) ✓; NITs (`SHA256SUMS` `|| stop` + `sha256sum -c` self-check before `REBUILD_OK`; the
unit-level `r1_sealed` check is now lexical; the repo W2-3 evidence path/SHA is recorded beside the `/work`
copy; the manifest notes the evidence JSON's stale stop_rule string) ✓. The CLI genuinely supports
`--classification` (verified in `dataset.py`'s argparse) and the EVIDENCE-only `table_sha256` is produced by
`_write_table`; logs are outside `OUT`, `OUT` is not pre-created (the code creates it with `exist_ok=False` under
`umask 077`), and a STOP preserves `OUT`/logs. Good round.

**But the unit still cannot run as written — two guaranteed STOPs, plus one availability risk:**

1. **BLOCKING — the classification sidecar path is on the wrong tree.** `CLASSIFICATION` is
   `$CHECKOUT/results/r1/evidence/C3_sweep_classification_20261028.json` (L16; the PLAN's command block likewise
   shows the repo-relative path under the checkout), but the reviewed `evidence_classification()` does
   `root = Path(paper_root).resolve(); sidecar = Path(sidecar_path).resolve(); if not sidecar.is_relative_to(root)
   or not index_path.is_relative_to(root): raise ValueError('classification and index must be inside repository')`.
   The checkout (`/work/.../w2_v3`) is not under the paper root (`/ceph/.../agent_paper_B`), so `build-sweep`
   exits non-zero immediately → the unit STOPs. *Fix:* point `--classification` at
   `$PAPER_ROOT/results/r1/evidence/C3_sweep_classification_20261028.json` (same sidecar, sha still
   `bb6d891c…`) and check **that** copy (exists + sha) before the build; keep the checkout copy only as a
   provenance record if wanted.
2. **BLOCKING — the repo-evidence check (L40) false-STOPs the unit before the build.** The unit verifies
   `git -C "$CHECKOUT" ls-files --error-unmatch docs/r1/reports/w2_3_check_20261115/w2_3_check_20261115.json`,
   but the checkout HEAD is pinned to the reviewed code commit `d8aa9561`, and the W2-3 evidence JSON was added
   later, at `03d742cf` (which is a **descendant** of `d8aa9561`: the evidence JSON is absent from the
   `d8aa9561` tree — verified with `git ls-tree`). The `ls-files` failure leaves the command substitution empty,
   so the unit STOPs with "repo W2-3 evidence copy missing/mismatched" before anything runs. *Fix:* drop the
   checkout-copy requirement — record the repo path/SHA in the manifest (it already does) and use the pinned
   `/work` copy (sha `b11217d0…`) as the input; if a repo copy must be verified, verify the copy from the
   branch that actually has it, not the code checkout.
3. **MAJOR risk — the paper-root clone may not contain the classification sidecar/PLAN row.** The paper root is
   the sweep-run clone (25 Oct era) while the `R1-SWEEP1-CLASSIFY` sidecar/PLAN row are 28 Oct artifacts; the
   code additionally verifies the closure over `docs/r1/PLAN.md` (the row must contain the sidecar's
   repo-relative path and sha) and `_verify_published` (PLAN/authorization/index/sidecar committed in the paper
   root's git). This is probably why round 2 used the checkout copy — but the code forbids that. *Fix:* before
   the build, pre-check `$PAPER_ROOT/results/r1/evidence/C3_sweep_classification_20261028.json` (exists + sha)
   and the `R1-SWEEP1-CLASSIFY` row in `$PAPER_ROOT/docs/r1/PLAN.md`; if the paper-root clone predates them, the
   EVIDENCE-label route needs a reviewed decision (writing the four classification artifacts into `/ceph` would
   break this unit's read-only promise; running without `--classification` would record the known runner-defect
   label — the author's row says that is not acceptable). This must be resolved before running.

**Minor (fold in with the above):** (i) the PLAN command block should show the classification path as the
paper-root copy, and its "Output" paragraph ("the unit creates it 0700") should say the reviewed code creates
`OUT` in classification mode while the unit creates only the parents and the logs dir; (ii) the R5 assertion
hardcodes 288/20 — read them from the pinned evidence JSON instead (and keep the hardcoded values as a cross-
check); (iii) add a post-build `git -C "$CHECKOUT" status --porcelain` check (STOP if the build changed any
tracked file) to substantiate the read-only claim; (iv) record `build.json`'s `table_sha256` (the EVIDENCE-only
provenance) in the manifest too; (v) the 2 GiB `df` threshold is a guess — record the actual output size after
the run.

**Verdict:** the round-1 findings are substantially addressed, but the unit may **not** run on deepthought as
written: fix the classification path (paper-root sidecar + pre-check) and the false-STOP repo-evidence check,
and decide the paper-root availability question; then a quick re-check is enough.

VERDICT: NOT ACCEPTED

---

## Round 3 delta re-check (branch @ `7c85ff4e`; 16 Nov 2026, 00:45 CET)

**Scope.** Round 3 at HEAD `7c85ff4e` (worktree clean): `run_rebuild.sh` SHA-256
`304700d6d93b80ad3bbb8e500c1e6b271146bfdd10d18b571f6cb99787ec5a41` (150 lines), PLAN.md
`d7da6427c280fb073dff5ecbdeeb796c5f121ede043d0845b6cf22a09bc9170f` (75 lines). Read-only; nothing executed.

**(a) The two path fixes are correct.** `CLASSIFICATION` and the `--index` argument are now the paper-root copies
(`$PAPER_ROOT/results/r1/evidence/C3_sweep_classification_20261028.json`, `$PAPER_ROOT/results/r1/pilot/
C3_sweep_index_20261028T033315Z.json`), both pre-checked for existence and SHA (`bb6d891c…`, `812468e2…`), and
the checkout copies are no longer used. This satisfies the reviewed `evidence_classification()`'s
`sidecar.is_relative_to(paper_root)` / `index_path.is_relative_to(paper_root)` gate (the round-2 STOP), and the
index path equals the pinned `SWEEP1_INDEX_PATH` with the pinned SHA, so `build_from_sweep` does not divert to
`require_d8_confirmation()`. The `BUILD_CMD` string records the paper-root paths, the pre-checks run **before**
any output/log directory is created, and the round-2 false-STOP (repo evidence in the `d8aa9561` checkout) is gone
— the pinned `/work` copy remains the input and the repo path/SHA is recorded in the manifest. ✓

**(b) The paper-root availability pre-check + documented "author decision needed" STOP is the right behaviour for
the current state.** The unit now checks, read-only and before creating anything: paper-root `docs/r1/PLAN.md`
exists and carries the `R1-SWEEP1-CLASSIFY` row naming the sidecar, the sweep-1 authorization exists, the
paper-root index has SHA `812468e2…`, and the paper-root sidecar exists with SHA `bb6d891c…`; when they are absent
(today's deepthought paper root is the older sweep clone, and — per the host check — its HEAD and `origin/main`
lack the 28-Oct artifacts) it STOPs with "author main-merge decision needed" instead of producing the
runner-defect label. That is honest, actionable and side-effect-free, and the unit becomes executable the moment
the author provides an authoritative paper root — which is exactly the right gate. **Caveat (not a blocker):** the
pre-check is necessary but not sufficient — the reviewed code additionally runs `_verify_published()`, which
requires the paper root's `origin` remote, a fresh `refs/remotes/origin/main` equal to `origin main`, and the
working-tree PLAN/authorization/index/sidecar bytes to equal `origin/main:<path>` (and the evidence trees later);
so the "authoritative paper root" must be a clone whose `origin/main` carries the 28-Oct classification artifacts
and the evidence trees and is freshly fetched — the code verifies this with fail-visible STOPs, so no silent
bypass. Optional improvement: add a paper-root git/`origin`-freshness pre-check (and name the origin/main
requirement in the STOP message) for a clearer early refusal.

**Minors folded:** the round-2 minors are handled as described (PLAN command paths; R5 reading `ledgers`/
`runs_total` from the evidence with the 288×20 cross-check; the post-build `git status --porcelain` STOP; the
`df` pre-flight kept and the run will record the actual output size). Two small items remain: (i) the PLAN
"Output" paragraph still says "the unit creates it 0700 and refuses if it exists", contradicting the updated
Command paragraph (the reviewed code creates `OUT` with `exist_ok=False`; the unit creates only the parents/logs)
— fix the sentence; (ii) `build.json`'s EVIDENCE-only `table_sha256` is only conditionally asserted (L137) and is
not recorded in the manifest — the label is already asserted `EVIDENCE`, so make the assertion unconditional and
add `"table_sha256": build.get("table_sha256")` to the manifest; the absolute `SWEEP_INDEX` pre-check duplicates
the paper-root index check (same file — harmless, may be dropped).

**Verdict: accepted.** The unit is correct and ready; it may be executed once the author's paper-root decision is
made (execution is held until then, per the plan). Run today, it STOPs cleanly at the availability pre-check
without creating an output directory or producing the defect label.

VERDICT: ACCEPTED
