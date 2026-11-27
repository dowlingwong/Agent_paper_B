# D.3 G6 Y / Y(w) audit — independent tier-E review

**Reviewed tip:** `23119523` (`compute-d3-g6-audit-20261127`), base `origin/main` `30f9b0ce`.
**Unit record:** `docs/r1/reports/d3_g1_20261127/D3_G6_AUDIT_20261127.md`.
**Files reviewed:** `r1/c3/d3/audit.py` (new, 377 lines), `r1/tests/test_d3_audit_g6.py` (new, 154 lines).

Verdict: CHANGES REQUIRED

**Independence.** I am a fresh tier-E reviewer. I did not write this unit, I did not
work in the author's worktree or on the author's branch, and I did not modify
`23119523`. I read the diff in a separate worktree created from the reviewed tip,
and I ran the tests and the synthetic checks below myself.

## What I checked

1. **Seeds, K, Y.** `audit_seeds` (`r1/c3/d3/audit.py:85-90`) is
   `6700 + 10*(s-6201) + k`, `k = 1..10`, and refuses `s` outside 6201-6218. Endpoints
   are 6701-6710 (`s=6201`) and 6871-6880 (`s=6218`), the declared 6701-6880 block.
   `K = 10` (`:58`). `y_raw = fsum(metric(incumbent) - metric(start))/K` (`:234-247`)
   and `Y = y_raw / sigma_node` (`:248`), with `sigma_node` required positive and
   finite (`:278-279`). The primary row is the final snapshot at its actual `w_final`
   (`:301-317`); the `w = 5/10/15/20` rows are the descriptive `Y_w` rows
   (`:284-299`, `:324-326`). A missing point is `missing_w` with `y_raw`/`Y` `None`
   (`:286-288`), never imputed. `w = 0` and incumbent == start return `Y = 0.0` by
   rule without a runner call (`:228-231`).
2. **Snapshot validation and the config key.** `load_snapshot` requires the
   snapshot fields, the `r1_d3_snapshot/v1` schema, matching `stage`/`arm`/`node`/
   `instance_id`/`repetition`, a non-empty incumbent/start file map, and
   `config_sha256(contents) == payload["config_sha256"]` (`:101-123`). It imports
   `config_sha256` from `r1.c3.d3.snapshots` (`:53`), i.e. the snapshot module's
   per-file-digest key, not a hash of the text map. The w files are additionally
   cross-checked against `final.json`'s fields and their own `w` (`:290-292`).
3. **Cache.** Key `(node, config_sha256, audit_seed)` for both configurations
   (`Cache`, `:130-162`; `audit_config`, `:175-198`), shared by the caller across
   arms/repetitions/w points (`audit_campaign` passes one `cache`,
   `:293`, `:301`). A cached row without a `run_sha256` is refused
   (`:143-144`, `:152-153`); a fresh run without a `run_sha256` is a STOP
   (`:195-196`). Hits are disclosed per row (`:245-246`) and per run
   (`:241-242`).
4. **Records and paths.** `<out>/<stage>/<arm>/r<rep>/w<w>/<instance>.json`
   (`:294`), `Y_final.jsonl` (one primary row, `:319-323`), `Y_w.jsonl`
   (one row per point including `missing_w`, `:324-326`), `SHA256SUMS` (`:331-338`).
   An existing record is refused (`:295-296`, `:313-314`). The w20 alias is set
   when the final config equals the point's config (`:304-307`); a last-keep change
   gets a distinct `final/w<w>/<instance>.json` (`:308-316`). I exercised both paths.
5. **No label/evaluation/test read.** The module imports only hashing, JSON, the
   snapshot module and, lazily, `r1.c3.audit.run_config` (`:357-377`). It reads only
   `<campaign>/snapshots/*.json`, the cache file and its own output. `grep` over the
   module finds no label, evaluation, split or sealed-table read. The default runner
   is the accepted B.2 audit mechanism (`run_config`, `r1/c3/audit.py:272-349`).
6. **Parallel-safety claim.** The report states the limitation explicitly
   (`D3_G6_AUDIT_20261127.md:40-42`): the two JSONL row files are not locked, so the
   launcher must serialise their appends or merge per-instance rows. That is honest.

## Blocking findings

### B1 — the w-point alias performs a second, independent audit, so `Y_final` can disagree with the record it names

`audit_campaign` audits `final.json` unconditionally at `r1/c3/d3/audit.py:301`
and only afterwards decides to alias the w record (`:304-307`). When `w_final` is a
`W_POINTS` value and the final config equals that point's config, the primary
`Y_final` row is therefore a **second** `audit_snapshot` execution, not a reference
to the first. With the default `cache=None` the second execution calls the runner
again; the unit does not require a deterministic runner, so the primary row's
`runs`, `y_raw` and `Y` can differ from the w record that `audit_record` names.
This contradicts design §3.3 (“G6 writes one canonical audit row and both
references point at it … no duplicate audit”) and the declared equality of the
primary Y with the descriptive `Y(20)`.

I demonstrated it with a nondeterministic runner and a `w5/w10/w15/w20 + final@20`
campaign: the w20 row and the referenced record had `Y = 99.2969…`, the primary
`Y_final` row had `Y = 101.4396…`, and `alias_of_w` was still `20`. Even with a
deterministic runner the duplicate execution is a second audit the design forbids;
with a cache it is all hits and the values agree, but the unit defaults to no cache
and the tests use no cache.

Fix: decide the alias before auditing `final` (copy the w row's `y_raw`/`Y`/`runs`
and point `audit_record` at it), or make the alias path require a cache and refuse
a mismatch between the final row and the referenced record. Add a test with a
runner whose second call differs (or assert the runner was not called twice and
that `final["Y"] == w_row["Y"] == record["Y"]`). The current alias test
(`r1/tests/test_d3_audit_g6.py:120-130`) asserts only the path and never compares
`Y` or counts runner calls, so it cannot catch this.

### B2 — the default runner accepts a file-changing (divergent) audit run

`harness_runner` calls `run_config(..., stop_on_invalid=True)`
(`r1/c3/d3/audit.py:365-367`) and then only checks `success` and a finite metric
(`:370-374`). It never checks `row["changed_files"]`. The accepted B.2 audit uses
`stop_on_failure=True` and treats `changed_files is not False` as an invalid audit
result (`r1/c3/audit.py:356` and `:1290-1295`). A run that mutates the copied node's
editable files is therefore accepted here, and because `run_config` reuses one node
copy for all seeds, the remaining seeds run on the mutated copy; the reported metric
need not belong to the audited configuration. The design §3.1 says the audit runs
“as `r1/c3/audit.py` runs B.2 audits”, and the unit's own report says a failed seed
run is a STOP.

Fix: reject `row["changed_files"]` in the wrapper before appending the `Run`
(`:369-374`). Passing `stop_on_failure=True` alone is **not** sufficient: if the
changed-file run is the last seed, `run_config` still returns all ten rows
(`r1/c3/audit.py:352-360`) and `audit_config`'s seed-set check (`:190-191`) would
accept it. The explicit `changed_files` check is the robust fix. Add a test. Also
raise `AuditStop`, not the raw `RuntimeError` that `run_config` emits, so a driver
that catches the declared STOP type sees the failure.

## Non-blocking minors

- **M1 (w = 0 record path).** For `w_final = 0` the code takes the `else` branch and
  writes `final/w0/<instance>.json` (`r1/c3/d3/audit.py:308-316`); I confirmed the
  file is created. Design §3.3 says “For w_final = 0 the canonical record is
  `final.json`, Y_final = 0, no audit path” and “an audit path is written only for
  w > 0”. The record is marked `audited=False`, `rule="w=0"`, so the value is
  harmless, but the path violates the design. Suppress it or record the deviation.
- **M2 (final vs campaign directory).** The module docstring says the audit refuses
  a snapshot “whose declared fields differ from the campaign directory”
  (`:22-23`), but `audit_campaign` never compares `final.json`'s `stage`/`arm`/
  `node`/`repetition`/`instance_id` to `campaign_dir`'s path (`:269-277`). The w
  files are checked against `final`, not against the directory. A misplaced
  `final.json` would be audited under its own declared path and instance seeds.
- **M3 (start-config consistency).** The w and final snapshots are not checked to
  carry the same `start_config`; the alias compares only incumbent configs
  (`:304-305`). A w row and the final row with the same incumbent but different
  baselines can be aliased. (This is a second way B1 can produce a mismatched
  reference.) The snapshot module writes one `start_config`, so this is defensive.
- **M4 (w beyond the final).** The audit does not check `w <= w_final` or
  `worker_runs == w`. A stray `w10.json` in a campaign whose `final.json` is at
  `w = 7` would be audited, producing a descriptive point the campaign never
  reached. The G1 writer should not create one; the audit should refuse it to keep
  “missing points are never imputed”.
- **M5 (cache conflicts).** `Cache.__init__` silently keeps the last row for a
  duplicate `(node, config_sha256, seed)` key; I confirmed two rows with different
  metrics/`run_sha256` resolve to the second with no STOP (`:136-145`). It also does
  not re-check `math.isfinite(metric)` for cached rows, and a row missing the
  `run_sha256` key raises `KeyError` rather than `AuditStop`. The design's
  provenance rule (“a hit is reused only if the source record and config sha still
  match”) argues for refusing a conflicting duplicate.
- **M6 (runner STOP type / test coverage).** `harness_runner` is untested; the eight
  tests all inject a synthetic runner. A `run_config` failure surfaces as
  `RuntimeError` (`r1/c3/audit.py:345-349`), not the unit's `AuditStop`, and the
  `tmp` directory must already exist. Worth a small wrapper test.
- **M7 (docstring overclaims).** The module docstring says the cache “refuses to mix
  an environment change into one cache” (`:37-38`), but `Cache` has no environment
  field and cannot refuse it; the report correctly defers this to the launcher. The
  docstring also says the launcher “may parallelise the 18 instances itself”
  (`:40-41`) without repeating the report's warning that the JSONL rows and
  `SHA256SUMS` are not parallel-safe. The report itself is honest
  (`D3_G6_AUDIT_20261127.md:40-42`), so this is wording only.
- **M8 (full-suite id-list sha).** The counts and the id lists are right (see
  below), but I could not reproduce the stated id-list sha256
  `971166036fa365bcb10f01f051c756a7b90c1e94e0b0c1637bedcbd28b7c1f19` from the
  supplied logs with any standard normalization. The sorted stripped-id list hashes
  to `826c73490f5ce27d8acf4b3f8b9edcf41b5fec7e8fb457eb95aec2d500411ee1`; the sorted
  raw FAILED/ERROR lines hash to
  `f26e3093743cb64271b39707b76bd4bb4128daa4d53a8c748c8333e3cdbe08c5`. Please state
  the exact file/normalization or correct the value; the substantive
  “zero new failures” claim is independently verified.
- **M9 (minor record fields).** The audit rows do not carry `instance_seed`; the G7
  builder can derive it from `instance_id`. `w_actual` is recorded but not required
  to equal `w`; a non-integer `w`/`w_actual` is silently truncated by `int()`. These
  are defensive only.

## Tests I ran

From my own worktree at `23119523`, with
`AR_HARNESS_ROOT=/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/harness9bb`
and `/private/var/folders/y6/2zvmjscx2s18w96j7qx32nnr0000gn/T/opencode/d3venv/bin/python`:

- `r1/tests/test_d3_audit_g6.py` — **8 passed**.
- `r1/tests/test_d3_g1_snapshots.py` — **18 passed**.
- `r1/tests/test_d3_g1_chunk.py` — **9 passed**.
- The three together — **35 passed** in 1.92 s.

Full-suite comparison (I did not rerun the full 12-minute suite; I checked the
supplied logs):

- tip `g6_tip_suite.log`: **108 failed, 4922 passed, 161 skipped, 3 errors, 71
  subtests**.
- base `adapter_base_suite.log` (`98c571d2`): **108 failed, 4914 passed, 161
  skipped, 3 errors, 71 subtests**.
- The sorted FAILED/ERROR id lists are byte-identical: **111 ids**, same count and
  same ids; `diff` is empty. `git diff 98c571d2 30f9b0ce` is docs-only, so the base
  code is the reviewed base. **+8 passed, zero new failures** is correct. Only the
  stated id-list sha256 is not reproducible (M8).

## Assessment

The seeds, K, the Y formula, the primary/descriptive split, `missing_w`, the
`w = 0` rule, the snapshot self-hash, the `config_sha256` key match, the cache key and
hit disclosure, and the record layout are all correct and well tested. The two
blocking issues are about the primary outcome's provenance: the alias path can
publish a `Y_final` that is not the audit it names (B1), and the production runner
accepts a file-changing run that the accepted B.2 mechanism rejects (B2). Both are
small, local fixes with clear tests. I would re-check only the diff after they are
made.

**Verdict: CHANGES REQUIRED** for B1 and B2. M1-M9 do not block acceptance on their
own, but M1 and M5 should be settled in the same pass.
