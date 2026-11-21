Reviewed base: `985dd45d` (published `main`); accepted at `db7f344d6ac372737444db5ab036d370543ea65f`

# Independent review record — the sweep-2 audit unit: batch extraction, the audit's sweep-2 mode, the sweep-2 integrity check, and the deepthought B.2 addendum draft

**Unit.** On `mac-s2-audit-20261121`: `r1/c3/sweep2_batch.py` (new), the sweep-2 profile of `r1/c3/audit.py`, `sweep2_integrity` in
`r1/c3/release_checks.py`, `r1/tests/test_c3_sweep2_audit.py`, one updated assertion in `r1/tests/test_c3_release.py`,
`docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md` (approved: false) and `docs/r1/reports/s2_audit_20261121/S2_AUDIT_UNIT_20261121.md`.
Authority: R1-SWEEP2-SETTINGS (2), R1-SWEEP2-RELEASE-DECISIONS (REL-CODE A), R1-S2-LABELS-TRAINDEV-RELEASE (`release.py` pinned at
`a9d8ff5e`, not edited); the queue of 21 Nov 2026 (22:44), item 1.

**Process.** One independent reviewer for all three rounds, read-only, synthetic data only (no label, evaluation, sealed or table
file opened), scratch under `/tmp/rev_s2a/` moved to its `_to_delete/`. Round 1 found no blocking defect and four majors (the batch
not bound to the signature, `approved:` not enforced, R1-SWEEP-HOST-HTC missing from D1, no table-differs STOP) and fourteen minors;
round 2 accepted with three minors (fixed in `db7f344d`); round 3 confirmed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `2ae7cce5` | NOT ACCEPTED (M1–M4; minors 1–14) |
| 2 | `b6ec0689` | ACCEPTED (minors 1–3) |
| 3 | `db7f344d` | CONFIRMED |

**Open items.** Author decisions D1–D6 in the draft (D1: the start row R1-SWEEP2-B2-GO, amending R1-SWEEP-HOST-HTC and R1-SWEEP2-B2-DRAFT and lifting R1-B2-DECOUPLE's "does not start" for sweep 2). Before signature: precondition 2 on deepthought (extract, build-sweep, counts, `verify --sealed`), the four sha256 pins and the counts entered, and the independent precondition-2 review. Residual risk (round 2): the sealed chunk layout, manifest fields and the collector harness `dirty: false` were taken from the code that wrote them, not from a real chunk; any mismatch fails closed at precondition 2.

## Round 1 (`2ae7cce5`)

> **NOT ACCEPTED**
>
> I found no blocking defect. The code works, sweep 1's behaviour is unchanged, and the release path reaches the new check correctly. Four MAJOR findings need a small revision before the author signs. Two of them are code changes to what the guards enforce, so the commit pinned in the addendum would need re-review anyway.
>
> ## What I checked and found sound
> - **Seal layout and fields match the code that wrote them.**
>   - Sealed tree: `job_record.json`, the `SHA256SUMS` that `seal` rewrites over every extracted file, then `SEAL_RECEIPT.json` (not covered by the sums).
>   - Manifest fields from `e1b_collect` and `collector_argv`: noise source dict, `b2_audits` "none", `audit_seeds` 0, nodes `[node]`.
>   - Root ledgers at `work/roots/<inst>/root_trials.jsonl`, start files at `out/roots/<inst>.json`.
>   - Chunk ids match the published `collection_counts.json`, and the pinned authorization, noise and counts hashes match the repo.
>   - The merged mode manifest passes `dataset.sweep_sources` for the right reasons. Noise values are compared with the pinned D28 file and only the path is rewritten. `launch_provenance` is absent on both sides (None == None). There is no `failures/` dir in the batch, and extract refuses chunk-level failures. Each mode has 144 ledgers in sweep 1's node order.
>   - The admitted R1-SWEEP2-RTE-DIAG chunks (which have `stop` and `out/worker_failure.json`) pass, through the pinned record hashes in the counts file.
> - **Sweep 1 is exactly unchanged.**
>   - `_completion` key order equals the real `docs/r1/reports/b2_audit_20261119/evidence_completion.json`.
>   - The real sweep-1 `environment.json` has no `source` key.
>   - `b2_addendum` messages and tokens for sweep 1 are the same; the CLI differs only in its error text.
> - **Lock and readers.** `evidence_tier` still treats the run log as T0 (prefix `r1.c3_audit_completion/`). `sft_data.LabelBlockSource` and `release.open_partition` accept a `/4` completion.
> - **Positive round trip.** My own probe ran `verify_evidence_completion(source='sweep2')` on a synthetic audit and it passes; the unit's tests have no positive case.
> - **Release path.** `release.py` equals `a9d8ff5e`. `python -m r1.c3.release --source sweep2 --paper-root P --index I` calls `sweep2_integrity(table, audit, paper_root=, index=)`; adding `--classification` gives a TypeError, which STOPs safely.
> - **Stale `origin/main` in `_sweep2_batch_published` does not matter.** The check then calls `b2_addendum` → `_published_bytes_ref`, which runs the `ls-remote` check and STOPs if the ref is stale. On this unpublished branch it correctly refuses.
> - **Tests.** The 18 new tests pass. Existing release, evidence_split_blocks, evidence_authorization, evidence_guards, e2_environment_basis and audit tests: 115 passed.
>
> ## MAJOR
>
> **M1. Nothing in code ties the batch's contents to the author's signature; `verify` only checks the batch against itself.**
> - Where: `r1/c3/sweep2_batch.py:28-30` (docstring), `:292-333`; `r1/c3/audit.py:868-895`, `:1060-1088`.
> - My probe changed a ledger byte, fixed its `EXTRACT.json` entry and rebuilt the index with `build_index`; `verify` passed.
> - For sweep 1, the index and manifests were bound to the published sidecar and the original git blobs. For sweep 2 nothing published binds the batch, so a change between `extract` and the audit goes undetected.
> - The draft lists the index and EXTRACT sha256 as pins (`DRAFT:145-146`), but no code checks them.
> - Fix:
>   - For sweep 2, have `b2_addendum` (or `_sweep2_plan`) require `_digest(index)`, the EXTRACT sha256 and the table's `proposals`/`configs` sha256 in the addendum text. Better still, publish the index and `EXTRACT.json` on main (B1 (a) parity) and compare their bytes through `_published_bytes`.
>   - Have `verify` check `EXTRACT.chunks[*].job_record_sha256` against the published `docs/r1/reports/sweep2_20261116/sweep2_report_20261121/collection_counts.json` (sha `3e29382b…`).
>   - Optionally add a `verify --sealed` that re-derives the batch from the sealed tree without writing.
>   - Reword the docstring's "the batch is checked wherever it is used".
>
> **M2. The addendum's `approved:` field is not enforced.**
> - Where: `docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md:121`, `:21`; `r1/c3/audit.py:1060-1088`.
> - The template ships `approved: false` and says "Set `approved: true` yourself", but `b2_addendum` only looks for substrings. An addendum committed with `approved: false` would authorize the run.
> - Fix: for sweep 2, require exactly one line `approved: true` and refuse otherwise (optionally also `label: EVIDENCE` and `sweep2_run_id: s2ev-20261119-a`), and add a test.
>
> **M3. D1 leaves out the signed row that conflicts most directly.**
> - Where: `DRAFT:27-40`.
> - `R1-SWEEP-HOST-HTC` (PLAN:1201) says that from sweep 2 on, all C3 label sweeps, including sweep 2's B.2 audit, run as HTCondor jobs, with CPU audits on one fixed HTCondor CPU node type. R1-B2-GO amended the host for sweep 1 only.
> - The proposed start row amends only R1-SWEEP2-B2-DRAFT. It also cites R1-MAIN-PROPOSER (f), which is marked *(proposed)* and was superseded by R1-SWEEP-HOST-HTC.
> - Fix:
>   - Name R1-SWEEP-HOST-HTC in D1 and in the start-row text ("Amends R1-SWEEP-HOST-HTC and R1-SWEEP2-B2-DRAFT for this audit").
>   - Say explicitly that the row lifts R1-B2-DECOUPLE's "does not start" for sweep 2.
>   - Optionally require the token `R1-SWEEP-HOST-HTC` in the start-row check at `audit.py:1083`.
>
> **M4. The draft has no STOP matching sweep 1's "host table differs from the dry run's".**
> - Where: `DRAFT:206-216`, precondition 2 at `:88-101`.
> - Precondition-2 values are only "recorded", and the 17 Nov draft's independent table review is gone. The unit report says this first run is also the only check of the layout assumptions.
> - Fix:
>   - Add a STOP: the index, EXTRACT, `proposals`/`configs` sha256 or the counts at audit time differ from the addendum's values (enforced by M1).
>   - Require a short independent review of the precondition-2 output (sha256s and counts, no labels) before signature.
>
> ## MINOR
> 1. **No D8 check before reading sealed ledgers** (`sweep2_batch.py:202-206`). Call `require_d8_confirmation()` at the start of `extract`, as the other sweep-2 readers do.
> 2. **Ledger files with a suffix are dropped** (`sweep2_batch.py:254`). `dataset` reads `*/root_trials.jsonl*`, but extract copies only `root_trials.jsonl`; my probe shows a listed `root_trials.jsonl.1` is silently skipped. Refuse any such SUMS entry, or copy all matches.
> 3. **Collector harness dirty flag not checked** (`sweep2_batch.py:170`); my probe passes with `dirty: true`. Require `harness.dirty is False`.
> 4. **`action_versions` not compared across chunks** (`sweep2_batch.py:60-62`). It is absent from `COMMON_KEYS`, so the eight chunks are not required to agree on the declared new-campaign versions. Add it, and `manager` equality across the two modes.
> 5. **Stopped chunks are not cross-checked** (`sweep2_batch.py:118-130`). Any record with `stop` is accepted if counted. Cross-check the set of stopped chunks against `counts["admitted_diagnosed_records"]`.
> 6. **Planted `EXTRACT.json` escapes the extra-file check** (`sweep2_batch.py:311-312`). The name filter applies at any depth; my probe shows a planted `sweeps/none/EXTRACT.json` is ignored. Compare the relative path at top level.
> 7. **Index hash depends on the operator's path spelling** (`sweep2_batch.py:270`). `sealed_run_dir` is the path string as typed, so a second party cannot reproduce the index sha with a different spelling. Store a constant or `resolve()`.
> 8. **Harness-equivalence paths are narrower than what the audit imports** (`audit.py:156`). The audit imports `src/autoresearch/nodes` (registry), `manager/base.py` and `common`; `uv.lock` is also outside the list. In fact the real diff touches none of these. Widen the paths. Also, the verifier trusts the recorded `diff: empty` (`audit.py:1235-1237`); re-run the check where the harness is available, or record the full diff output.
> 9. **Start row found by line prefix** (`audit.py:1083`). `line.startswith('| R1-SWEEP2-B2-GO |')` matches anywhere in PLAN, including fenced or quoted text (the same weakness as the R1-B2-GO check). Use `release.author_rows`.
> 10. **D2's description of the harness diff is inaccurate** (`DRAFT:49-50`). The diff also touches `control_plane/campaign.py`, and `HARNESS_DEFAULTS_CHECK_20261120.md` only checked `configs`, `nodes` and `harness`. Correct the wording.
> 11. **D3 wording** (`DRAFT:60-61`). The image's harness Python is 3.13.18 (`s5_identity.txt`), not 3.13.15. Disclose the patch-level difference and cite the strongest fact: the image's `harness_lock_sha256` equals the e1 basis `uv.lock` (`dd42d018…`).
> 12. **Time estimate** (`DRAFT:159-166`).
>     - Fair facts: 4,660 seed runs in 22 min 44 s is correct; 5,287 sweep-1 successes is correct; the eligible count is a placeholder.
>     - Flawed reasoning: "5,300 vs 5,287 successful trials, so the same order" does not follow. Seed runs depend on unique configurations after de-duplication, and in sweep 1, 3,274 of 4,999 proposals were duplicates.
>     - Inconsistency: a fixed 10,800 s deadline is stated next to `--deadline <operator>`.
>     - Fix: drop or replace the argument (unique configurations are bounded by each node's config grid), set the deadline from the counts (for example max(3 h, 2.5 × projection)), and note that hashing the full sealed `work/` trees may take longer than "minutes".
> 13. **Overwrite and docs-overlay gaps.** `build-sweep` without a classification uses `exist_ok=True` (`dataset.py:494`), so precondition 2 should require a new table directory. Also add sweep 1's "PLAN.md is not changed on main while the audit runs".
> 14. **Test gaps.**
>     - No test for a stopped (admitted) chunk record.
>     - No positive sweep-2 verifier round trip.
>     - The git branch of `_sweep2_batch_published` is untested.
>     - The tamper test's wording suggests `verify` catches forging in general, which M1's probe disproves.
>     - Fix: add these tests and a test that pins the M1 behaviour.
>
> ## Notes
> - Read-only: nothing was modified in `/tmp/pb/wt/s2audit` or `/tmp/pb/wt/t1h`, nothing committed, and no label, evaluation, sealed or table file was opened. The non-label records I read were the sweep-1 index, the b2_audit `environment.json` and the key list of `evidence_completion.json`, and the published `collection_counts.json` and `chunks_summary.json`.
> - My probes and scratch are in `/tmp/rev_s2a/_to_delete/` (`probes/test_probe_s2.py`, `probes/test_probe_verify_s2.py`, `t/`); nothing was deleted.

## Round 2 (`b6ec0689`)

> **ACCEPTED** (round 2, `2ae7cce5..b6ec0689`)
>
> The round-2 commit fixes all four MAJOR findings and all 14 minors from round 1. I found nothing BLOCKING or MAJOR. Three MINOR points remain; they can go in a follow-up or with the fill-in of the addendum.
>
> Targeted tests pass: 142 across `test_c3_sweep2_audit` (27), `release`, `evidence_split_blocks`, `evidence_authorization`, `evidence_guards`, `e2_environment_basis` and `audit`.
>
> ## Round-1 findings, checked against the diff
>
> - **M1 (batch contents not bound to the signature): fixed.**
>   - For sweep 2, `b2_addendum` now requires four full sha256 pins: index, `EXTRACT.json`, table `proposals.jsonl` and `configs.json`.
>   - `_sweep2_pins_match` runs in `evidence_run` after the plan and before the resource check and `mkdir`. It runs again in `verify_evidence_completion`, against a recorded addendum that must equal a fresh `b2_addendum`, so the pins are re-checked too.
>   - `verify` now checks the chunk record sha256s and the admitted set against the published `collection_counts.json`, whose sha256 is pinned.
>   - `verify --sealed` re-derives the whole batch from the sealed tree without writing. `SEALED_RUN_DIR` is now a constant, so a second party gets the same index sha256.
>   - The docstring now says `verify` checks internal consistency only. A test pins this: a consistent forgery passes `verify` and fails `verify_sealed`.
>   - The draft requires `verify --sealed` and an independent review of the precondition-2 output before signature.
> - **M2 (`approved:` not enforced): fixed.** The key block must read `approved: true`, `label: EVIDENCE`, the run id and the start ruling, with no key twice. In the draft's addendum part, the only `key:` lines are the key block itself, so the whole-file parse picks up nothing else.
> - **M3 (R1-SWEEP-HOST-HTC left out of D1): fixed.**
>   - D1 now names R1-SWEEP-HOST-HTC as the most direct conflict.
>   - It says R1-MAIN-PROPOSER (f) was only proposed and was superseded.
>   - The proposed start row amends R1-SWEEP-HOST-HTC and lifts R1-B2-DECOUPLE's "does not start" for sweep 2.
>   - The code finds the row with `release.author_rows`, requires exactly one, and requires the run id, R1-SWEEP-HOST-HTC, R1-B2-DECOUPLE and B6 (a), B4 (a), B1 (a).
> - **M4 (no STOP like sweep 1's "host table differs"): fixed.** There is now a STOP for pins or counts that differ (the code enforces the four sha256s), a STOP if PLAN changes during the audit, and the precondition-2 review.
> - **Minors 1–14: all addressed.**
>   - Code: D8 check at the start of `extract`; suffixed ledgers refused; collector harness must be clean; `action_versions` added to the common keys; one manager across both modes.
>   - More code: stopped chunks cross-checked against the admitted records, in both `extract` and `verify`; top-level relative path in the extra-file check; dangling symlinks now counted.
>   - Harness check: the paths now include `uv.lock`, `nodes`, `common` and `manager/base.py`. I confirmed the diff over them is empty in `/tmp/pb/wt/t1h`. The verifier re-runs the check where the harness is present.
>   - Draft: Python 3.13.18 vs 3.13.15 disclosed, with the `harness_lock` equal to the e1 `uv.lock` `dd42d018…`; the estimate is now counts-based with deadline `max(10,800 s, 2.5 × T)`; new table directory required; the extra tests.
>   - Sweep 1 is still unchanged: its `b2_addendum` return has no `pins` key.
>
> ## MINOR
>
> 1. **The D2 wording in the draft is wrong** (`docs/r1/proposals/C3_SWEEP2_B2_ADDENDUM_DRAFT_20261121.md:70`). It says "The audit's seed runs import none of them." In fact `src/autoresearch/manager/base.py:6` imports `autoresearch.memory.summarizer`, which changes between `6adf3859` and `a3fedbbd`. The change only adds Track S display modes for memory lines, which a no-edit audit run never uses, so the labels are not affected. But the claim is false, and the check in `SWEEP2_EQUAL_PATHS` (`r1/c3/audit.py:156`) covers only the listed paths, not what they import.
>    - Fix: reword to "imported via `manager/base.py`; the diff adds opt-in memory-display modes only, unused by the audit". Optionally compare the blobs of every `autoresearch.*` module the audit loads at both commits.
> 2. **`extract` does not check the sealed path it is given** (`r1/c3/sweep2_batch.py:233`, `:310`). It records `SEALED_RUN_DIR` whatever path was passed, so extracting from a copy elsewhere would record a false source.
>    - Fix: refuse unless `Path(sealed_run_dir).resolve() == Path(SEALED_RUN_DIR).resolve()` (tests can monkeypatch the constant), or record both paths.
> 3. **`precondition2_review` is cited but not checked by code** (`DRAFT:172`).
>    - Fix (optional): require it in the key block, published on `origin/main` and ending in an ACCEPTED verdict, as is already done for the code review.
>
> **Residual risk.** The new collector-harness `dirty is False` requirement could not be checked against real chunk manifests on the desk. If they record a dirty harness, it fails closed: `extract` STOPs at precondition 2 and the author is told.
>
> Read-only throughout: both worktrees are unchanged and nothing was committed or deleted. All my scratch, round 1 and round 2, is in `/tmp/rev_s2a/_to_delete/`.

## Round 3 (`db7f344d`)

> **CONFIRMED** (`b6ec0689..db7f344d`)
>
> All three round-2 minors are fixed as described, and I found no new findings. The targeted tests pass: 76 across `test_c3_sweep2_audit` (28), `test_c3_evidence_authorization` and `test_c3_release`.
>
> 1. **D2 wording.** The draft at line 70 now says that `memory/summarizer.py` is imported via `manager/base.py`, that its diff adds opt-in Track S display modes only, and that the run-time check covers the listed paths, not what they import. This matches what I found in the harness diff.
> 2. **Sealed path.** `extract` now refuses unless the given path resolves to `SEALED_RUN_DIR` (`r1/c3/sweep2_batch.py:236-237`). The check sits right after the D8 check and before anything is read. `verify --sealed` goes through the same check. A symlinked path that resolves correctly is still refused by the later `_no_links` check. The fixture now monkeypatches the constant, and the new `sealed_copy` refusal test exercises the check.
> 3. **Precondition-2 review** (`r1/c3/audit.py:1112-1120`).
>    - The path must be repository-relative under `docs/r1/reviews/` and end in `.md`; an empty or missing key is refused.
>    - The file is read from `origin/main` through `_published_bytes`.
>    - It needs an exact `Verdict: ACCEPTED` line and all four pin values.
>    - It is recorded as `{path, sha256}` in the addendum record, so `verify_evidence_completion` re-checks it through the equality test on the recorded addendum.
>    - Tests cover the verdict, a missing pin and a bad path.
>
> Note: a later edit of that review file on `main` would make the audit unconsumable, as an edit of the addendum would. That fails closed and is consistent with the rest of the design.
>
> Read-only throughout: the worktree is clean and nothing was committed or deleted. Scratch is in `/tmp/rev_s2a/_to_delete/` (round 3 under `r3/`).

---

Code-Commit: db7f344d6ac372737444db5ab036d370543ea65f
Verdict: ACCEPTED

Accepted: the sweep-2 batch step, the audit's sweep-2 mode and the sweep-2 integrity check at `db7f344d`; the addendum remains a draft (approved: false).
