# D.3 G6 Y / Y(w) audit — R2 independent tier-E review

**Reviewed tip:** `b4b15ddb` (`compute-d3-g6-audit-20261127`), base `origin/main` `30f9b0ce`
(the code at `30f9b0ce` is identical to `98c571d2`; the only `98c571d2..30f9b0ce` diff is docs).
**R1 review:** `docs/r1/reviews/D3_G6_AUDIT_REVIEW_20261127.md` (CHANGES REQUIRED, tip `23119523`).
**Unit record:** `docs/r1/reports/d3_g1_20261127/D3_G6_AUDIT_20261127.md`.
**Diff since R1:** `23119523..b4b15ddb`, 3 files, +106/−25.

Verdict: ACCEPTED

**Independence.** I am the fresh tier-E reviewer from R1. I did not write this unit and
did not modify the author's worktree or branch. I read the R2 diff and the full
`r1/c3/d3/audit.py` in a separate worktree at `b4b15ddb`, and I ran the focused tests
and the synthetic checks below myself.

## The two R1 blocking findings

### B1 (alias) — fixed

`audit_campaign` now decides the alias **before** any audit
(`r1/c3/d3/audit.py:317-325`): when `final_w` is an existing w point and the final
incumbent's `config_sha256` equals that row's, `final_row` is a `copy.deepcopy` of
the w row, with `ended_on` taken from `final.json`, `final=True`, `primary=True`,
`alias_of_w`, and `audit_record` pointing at the w record. There is no
`audit_snapshot(final)` call on this path, so the primary row cannot disagree with
the record it names. The non-alias path still audits the final and writes
`final/w<w>` only when the config differs.

I verified this independently, with a drifting runner and **no cache**: a
`w5 + w20 + final@20` campaign made exactly 4 runner calls (w5 incumbent, w5 start,
w20 incumbent, w20 start) and `final["Y"] == w20["Y"]`, `alias_of_w == 20`. I also
confirmed `final["record_sha256"]` equals the SHA-256 of the w record file. The new
test (`r1/tests/test_d3_audit_g6.py:122-149`) uses a `DriftingRunner` and a cache and
asserts `final["Y"] == w20["Y"]` and `runner.calls == 3`; it passes.

### B2 (production runner) — fixed

`harness_runner` now passes `stop_on_failure=True` and rejects a row whose
`changed_files` is not `False` before appending the `Run`
(`r1/c3/d3/audit.py:388-400`). With `stop_on_failure=True`, `run_config` breaks on
the first failed, file-changing or non-finite seed, so the wrapper sees the
offending row and raises `AuditStop`; `audit_config`'s seed-set check (`:194-195`)
catches a short list. The changed-file last-seed case is caught directly by the
`changed_files` check. (A non-numeric metric could still surface from
`run_config`'s own `stop_on_invalid` guard as a `RuntimeError`; the harness metric is
a float, so this is an edge case.) The new test
(`r1/tests/test_d3_audit_g6.py:204-210`) monkeypatches `r1.c3.audit.run_config` to
return a changed-file row and asserts the STOP. It passes.

## Minors taken in R2

- **w = 0.** `final_w == 0` now sets `audit_record = None` and writes no
  `final/w0` record (`r1/c3/d3/audit.py:329-331`); the test asserts
  `audit_record is None` (`r1/tests/test_d3_audit_g6.py:96-105`). I confirmed no
  `final/w0` file is created.
- **Campaign directory / instance.** `audit_campaign` refuses a campaign directory
  whose name differs from `final.json`'s `instance_id` (`:284-285`), then re-loads
  the final with the expected fields (`:286`).
- **Start-config consistency.** Every w snapshot's `start_config` must hash to the
  final's (`:306-307`); the test covers a differing start
  (`r1/tests/test_d3_audit_g6.py:186-192`).
- **w range and worker runs.** A w file above `final_w` is a STOP (`:304-305`);
  `audit_snapshot` refuses `worker_runs != w` when `worker_runs` is present
  (`:227-228`). The test covers both (`r1/tests/test_d3_audit_g6.py:175-184`).
- **Cache provenance.** A duplicate `(node, config_sha256, seed)` with a different
  `run_sha256` is a STOP, and a cached metric is checked finite
  (`:142-148`). The duplicate test (`r1/tests/test_d3_audit_g6.py:194-202`) passes;
  the non-finite path is code-reviewed but not separately tested.
- **Docstring.** The parallel sentence now says a JSONL line write is not atomic and
  the launcher serialises the cache/row appends (`:40-42`).

The seeds (`6700 + 10·(s−6201) + k`, 6701-6880), `K = 10`, the Y and Y(w) formulas,
the primary/descriptive split, `missing_w`, the snapshot `config_sha256` key, the
cache key, the record paths and `Y_final.jsonl`/`Y_w.jsonl`/`SHA256SUMS` are
unchanged from the R1-reviewed code and still correct.

## Remaining non-blocking minors

These do not change a Y value, a seed, an audit record or a STOP for a sealed
snapshot; they are defensive input-validation/documentation items.

- **Alias branch skips the final's `worker_runs`/`w_actual`.** The alias path
  deep-copies the w row (`:317-325`) and never calls `audit_snapshot(final)`, so a
  malformed `final.json` with `w=20`, `worker_runs=7` aliases without a STOP (I
  confirmed this). The w20 snapshot itself is checked, so the audited Y and record
  are unaffected; the final's `worker_runs` is redundant metadata. If every snapshot
  should be validated, call a small `_check_worker_runs(final, final_w)` before the
  alias.
- **No `final_w` upper bound.** `final_w` is not required to be in `0..20`; a
  malformed final at `w=25` would be audited at 25 and written as `final/w25`. The
  G1 writer's W = 20 forbids it; add `0 <= final_w <= 20` for defence.
- **Other final fields.** `ended_on` is copied to the primary row without checking
  the design's enum; `w_actual` is not checked; `REQUIRED_SNAPSHOT` does not include
  `worker_runs`, so a snapshot without it bypasses the `worker_runs` check. The G1
  snapshots carry these fields.
- **Report wording.** The report (`D3_G6_AUDIT_20261127.md:40-42`) still says “The
  append-only cache is safe for that” while the new docstring says JSONL writes are
  not atomic and the launcher serialises; the test bullet list still describes the
  old eight tests (it does say 12 passed); the full-suite section still cites tip
  `3256a126` and the `9711…` sha. Update when the `b4b15ddb` full-suite log exists.
- **Docstring environment sentence.** `:37-38` still says the cache “refuses to mix
  an environment change”; `Cache` has no environment field. The launcher's fresh
  cache file per environment record is the actual mechanism.

## Tests

From my own worktree at `b4b15ddb`, with
`AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb`
and `/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python`:

- `r1/tests/test_d3_audit_g6.py` — **12 passed**.
- `r1/tests/test_d3_g1_snapshots.py` — **18 passed**.
- `r1/tests/test_d3_g1_chunk.py` — **9 passed**.
- The three together — **39 passed** in 1.79 s.

Full-suite status: the `b4b15ddb` log
`/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/g6_fix_suite.log`
**does not exist yet**; the only full suite I found running is the adapter unit's
(`g1adapter` → `adapter_fix_suite.log`), not G6. I therefore rely on the focused
tests as the blocking evidence, as instructed. The base remains `98c571d2`
(108 failed / 4914 passed / 161 skipped / 3 errors); the `b4b15ddb` full-suite counts
are not yet available to compare.

## Assessment

The two R1 blocking findings are fixed and independently reproduced: the alias path
no longer performs a second audit, and the production runner rejects a changed-file
run. The R1 minors are taken, the focused suite is 12/12, and the snapshot/chunk
modules are unaffected (39/39 together). The remaining items above are defensive
validation and report wording; none changes the Y, the declared seeds, the audit
records or a STOP for a sealed G1 snapshot. I accept `b4b15ddb`.

**Verdict: ACCEPTED**
