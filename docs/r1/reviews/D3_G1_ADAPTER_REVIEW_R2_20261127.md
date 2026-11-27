# D.3 G1 adapter — independent tier-E re-review (R2)

**Reviewer.** Fresh, independent tier-E reviewer (subagent); I wrote the R1 review of this unit and did not
write the adapter, its tests, the chunk change or the constants artifact. Read-only on the reviewed branch:
no campaign, audit, GPU job, server, label, evaluation, split, sweep table or sealed file was read or run.
The only writes are this review, the review branch and a scratch worktree under the session's temporary
directory.

**Target.** `origin/compute-d3-g1-adapter-20261127` @
`4fc01ae8` (code at `2da347e2`; `4fc01ae8` is a docs-only commit that updates the unit record's
full-suite counts, verified by `git diff --stat 2da347e2..4fc01ae8` — one file, the unit record). R1
review: `docs/r1/reviews/D3_G1_ADAPTER_REVIEW_20261127.md` (`CHANGES REQUIRED`; four blocking findings).
Unit record: `docs/r1/reports/d3_g1_20261127/D3_G1_ADAPTER_20261127.md`; full-suite id list:
`docs/r1/reports/d3_g1_20261127/FULL_SUITE_FAILURE_IDS_20261127.txt`.

---

Verdict: ACCEPTED

---

## Summary

All four R1 blocking findings are fixed, and I reproduced the evidence at the fixed code:

- **B1 (FIXR3/EGATE `NameError`)** — `ManagerProposal`/`ManagerStatus` are top-level imports
  (`r1/c3/d3/adapter.py:71`) and the local import in `propose` is gone. The FIXR3 test now asserts 18
  successful rows per campaign, `j = {0,1,2}`, 18 rows and the worker-call count
  (`r1/tests/test_d3_adapter.py:256-260`). The campaign executes six 3-run steps, not eighteen failed
  1-run steps.
- **B2 (EGATE `incumbent_metrics`)** — `propose` uses `getattr(state.engine, "incumbent_metrics", None)`
  (`adapter.py:610`); the new EGATE test runs 18 campaigns and every sampled row succeeds
  (`test_d3_adapter.py:265-276`).
- **B3 (active-key validation)** — `validate` checks the path in `spec_node.editable_paths`
  (`adapter.py:629`), the symbol in `editable_symbols` (`:632`), a non-no-op old/new pair with
  `values_equal` (`:634`), and `inactive_key_in_proposal` against the current constants (`:637`) before
  `features.apply_edit`. The out-of-scope test charges only LLM calls and no worker run
  (`test_d3_adapter.py:290-300`).
- **B4 (tests did not detect B1/B2)** — the FIXR3 assertions above and the new EGATE test close that gap;
  the new out-of-scope test covers the validation refusal.

No remaining blocking finding. The fixed tip's full suite has the same 111 `FAILED`/`ERROR` ids as the
base, with the 13 new tests passing and no new failure.

## What I checked

- `25b0a355..2da347e2` in full (adapter, test module, unit record, new id-list file) and
  `2da347e2..4fc01ae8` (unit-record counts only); the code hashes at `4fc01ae8` equal those at
  `2da347e2`.
- The manifest/constants/arm/manager-selection half from R1 is unchanged: W = 20, cap = 80, trial
  budget 80, `append_only_summary`, verify 2/20000/vary, harness `9bb41680`, the seven nodes and seven
  D.3a arms; A1/A2 file vectors; `sigma_cmp` from the noise table; LADDER `eta = c * sigma_node`; A3/A5/A6
  refusals. No arm or seed substitution appears in the harness-arm path.
- `validate` semantics against revision 6c §3.5 and the harness E1 functions: `values_equal` is the
  harness comparison; `inactive_key_in_proposal` is the harness E1 active-key check and is called with the
  incumbent constants, as `run_real_campaign` calls it.
- The `ended_on` resolver change and the fixed-string bit-for-bit path (unchanged from R1).
- The fixed-tip full-suite log at `2da347e2` (code-identical to `4fc01ae8`):
  `/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/adapter_fix_suite.log`.

## R1 finding resolution

| R1 finding | Status | Evidence |
|---|---|---|
| B1 `ManagerProposal` scope / replicate runs fail | **Resolved** | Top-level imports `adapter.py:71`; `run_trial` `:656`; FIXR3 rows all successful, `j={0,1,2}`, 18 rows, 18 worker calls per campaign (`test_d3_adapter.py:256-260`); 13 adapter tests pass. |
| B2 EGATE `incumbent_metrics` | **Resolved** | `getattr` at `adapter.py:610`; EGATE test 18 campaigns with successful rows (`test_d3_adapter.py:265-276`). |
| B3 no active-key validation | **Resolved** | `adapter.py:625-638`; out-of-scope test gives `worker_runs = 0`, `llm_call_cap` for 18 campaigns, zero fixture-worker calls (`test_d3_adapter.py:290-300`). |
| B4 test could not detect B1/B2; no EGATE test | **Resolved** | Assertions above; EGATE and out-of-scope tests added; 13 tests / 288 focused. |

## Tests I ran

Worktree at `4fc01ae8`, `AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb`
(`9bb416805175149eb87b71f28d77530572aa4bce`, clean), Python 3.12.8, pytest 9.2.0:

- `r1/tests/test_d3_adapter.py`: **13 passed** in 2.50 s.
- The ten-module focused set: **288 passed** in 7.65 s.
- Fixed-tip full suite (`adapter_fix_suite.log`, `2da347e2`): **108 failed, 4927 passed, 161 skipped,
  3 errors**, 71 subtests, 692 s; base `98c571d2` **108 failed, 4914 passed, 161 skipped, 3 errors**,
  71 subtests. The 111 `FAILED`/`ERROR` ids are identical, sha256
  `971166036fa365bcb10f01f051c756a7b90c1e94e0b0c1637bedcbd28b7c1f19`; the committed id list has 111
  unique ids and its newline-joined id list hashes to that value.

## Remaining minors (non-blocking)

1. **The committed id list truncates parameterized ids at the first space.** The extraction rule
   (`FULL_SUITE_FAILURE_IDS_20261127.txt:3`) says "the `id` fields of lines matching
   `^(FAILED|ERROR) <id>`"; the file's implementation takes the first whitespace-delimited token, so six
   parameterized ids end at an internal space (e.g. `[W\x00-1-workload`). The list still has 111
   distinct, stable keys, the sha matches it, and the base/tip sets are identical, so the comparison holds;
   a future exact-id check should use `split(" - ", 1)` or pytest's machine-readable output. Update the
   rule wording or the ids when convenient.
2. **The unit record's "two synthetic whole-chunk tests" sentence (`:112`) is stale.** There are now four
   whole-chunk tests (A0, FIXR3, EGATE, out-of-scope); the named two are still accurate. Minor wording.
3. **The new out-of-scope test covers the path branch of `validate`.** The symbol-in-`editable_symbols`,
   `values_equal` no-op, and `inactive_key_in_proposal` branches are confirmed by code reading and the
   harness functions' own tests, but not directly exercised by this unit's tests. A small focused test
   (an inactive openml key and a no-op old/new) would close the gap; non-blocking.
4. **`validate` re-parses the node constants on every proposal** (`adapter.py:635`) instead of reusing the
   status's `current_constants`. Correctness is unaffected; performance only.

## Independence

I am a fresh, independent reviewer; I did not write the reviewed unit. I did not modify the author's branch
or worktree, did not amend or force-push, did not merge, and did not touch `main`. I did not run a
campaign, server, GPU job, or read a label, evaluation, test or sealed file. My only writes are this review
file, the new commit on the existing review branch, and a scratch worktree under the session's temporary
directory.
