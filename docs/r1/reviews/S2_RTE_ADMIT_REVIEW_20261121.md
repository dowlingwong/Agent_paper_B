# Independent review — R1-SWEEP2-RTE-DIAG collection admission (S2-RTE-ADMIT)

**Reviewer role:** fresh, independent, read-only reviewer (not the author, not the executing agent). **No job,
server, collection run or `condor_*` command was started; no git write was made.** The only file this review creates
is this uncommitted review file. Sealed chunks were read only (read-only SSH to
`deepthought.etp.kit.edu`, `sha256sum`-style re-verification of their `SHA256SUMS`; copies for the local probe were
made under `/private/tmp/rte_review.*` and never written back).

**Date/time of review:** 21 November 2026, 11:08–11:55 CET (Europe/Berlin).

**Unit under review:** branch `s2-rte-admit-20261121` @ **`a5d06f58`** (single commit; parent/base = published main
`d47d1008`), worktree `.claude-worktrees/s2-rte-admit-20261121`, clean before this review. Diagnosis evidence branch
`ops-sweep2-rte-diag-20261121` @ **`342b06eb`**. Sealed run `s2ev-20261119-a` (launch commit `4aac5209`), chunks under
`/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`.

| file | lines | SHA-256 |
|---|---:|---|
| `sweep2/s2_c2_lib.py` @ `a5d06f58` (base `d47d1008`: 1186 lines) | 1280 | `ef6c61044e2d738c632ca46b915eee21b55c49a53aef2df614f42f8a9e8b1e46` |
| `r1/tests/htcondor/test_s2_rte_admit.py` @ `a5d06f58` (new) | 60 | `eb62a38a67a859fe8be800c0ad21464a885d192dc4c3b300a7f7ad5e834a6663` |
| `docs/r1/PLAN.md` row `R1-SWEEP2-RTE-DIAG` @ `d47d1008` | — | (read at `d47d1008` lines 1349ff) |

Diff vs base: exactly 2 files, +162/−8 (`sweep2/s2_c2_lib.py` +110/−8; new test file +60). Nothing else changed.

**Tests were run with** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/_harness_venv/bin/python`
(Python 3.11.11, pytest 9.2.0), `-p no:cacheprovider`.

---

## 0. Verdict summary

**NOT ACCEPTED.** The unit is fail-closed, but on the **actual sealed chunks it admits none of the six trials** —
`collect_evidence` stops on the first diagnosed chunk before (and even if it reached) the admission check, and the
per-trial verification cannot match the sealed artifacts for four independent reasons:

- **F1 (blocker):** the stopped records' sealed `gates` are `{"status": "FAIL", "error": …}` with **no
  `node`/`memory_mode`**, so `collect_evidence` computes `key = (None, None)`, which is rejected at
  `s2_c2_lib.py:1177` before `_admitted_diagnosed_chunk` is ever called ("unexpected, stopped or duplicate chunk
  record"). Additionally, stopped records have **no `campaign_placement`**, so the next line that would run,
  `placement = record["campaign_placement"]` (`:1183`), is a `KeyError`.
- **F2 (blocker):** for the five ParserError trials the declared string is `yaml.parser.ParserError`, but the
  sealed `work/roots/<campaign>/art/trial-NNN/run.log` contains only
  `FAILURE_MESSAGE=ParserError: while parsing a flow mapping` — the qualified name exists in the committed
  diagnosis `traceback.txt` but **not anywhere in the sealed chunk**. The substring test therefore stops every
  ParserError chunk ("admitted trial exception differs").
- **F3 (blocker):** `openml_climate__s264` has **two** diagnosed runtime-error trials (t19, t20) in the **same
  campaign root**; the per-campaign rule requires the runtime-error row list to be exactly `[trial_id]` for each
  declared trial, so it can never admit both ("admitted trial ids differ").
- **F4 (blocker):** the result assembly still reads the **record's** gates, not the synthesized gates:
  `record["gates"]["roots"]` (`:1228`), `["llm_calls"]` (`:1233`), `["parse_failures"]` (`:1234`). For an admitted
  stopped record those keys do not exist → `KeyError` after F1–F3 are fixed.

Consequences: the four chunks remain STOPs, so the collection stays at 12/16 chunks and the R1-SWEEP2-RTE-DIAG (i)
outcome ("the four chunks are accepted and the collection covers all 16 chunks") is not achieved by this code as
written. Binding of the constants to the diagnosis is, however, correct (section 1). Accounting changes are
conceptually right but unreachable (section 5). Tests pass but exercise only a synthetic happy path that does not
resemble the real sealed records (section 6).

---

## 1. Binding to the diagnosis — **PASS**

I read the four sealed `job_record.json` files and the committed diagnosis
(`docs/r1/reports/sweep2_20261116/S2_SWEEP2_RTE_DIAG_20261121.md` + `sweep2_rte_diag_20261121/summary.json`) and
compared them programmatically against `RTE_DIAGNOSED`:

| chunk (declared = sealed `chunk_id`) | declared `record_sha256` | sealed `sha256sum` | `SHA256SUMS` line | declared `stop` = sealed stop | declared trials | diagnosis match |
|---|---|---|---|---|---|---|
| `openml_breast_w-append_only_summary` | `67510277…f4415` | identical | identical | yes | s145 t016 `yaml.parser.ParserError`; s155 t019 `TypeError` | yes |
| `openml_climate-append_only_summary` | `3b49670e…80c9c` | identical | identical | yes | s264 t019, t020 `yaml.parser.ParserError` | yes |
| `openml_credit_approval-append_only_summary` | `65fb201f…29ab4` | identical | identical | yes | s200 t011 `yaml.parser.ParserError` | yes |
| `openml_wdbc-append_only_summary` | `9fcf8936…bc871` | identical | identical | yes | s150 t020 `yaml.parser.ParserError` | yes |

- Chunk set, campaign ids, trial ids, and trial counts are **exactly** the six entries of the diagnosis
  `summary.json` (programmatic set comparison: 6 = 6, no extra, no missing). Five `class_weight` mapping
  `ParserError`s + one `max_depth: null` `TypeError` matches the diagnosis and the per-trial tracebacks/configs.
- All four records are `schema: s2_c2_job_record/1`, `run_id: s2ev-20261119-a`, `label: EVIDENCE`,
  `paper_commit: 4aac52092813b2b01ddb96cd7d135c390aeff645`, `finished_utc` present, frozen v1 image digest, and their
  `stop` strings are exactly the declared ones.
- The declared exceptions are faithful to the diagnosis: the committed `traceback.txt` for the ParserError trials
  ends in `yaml.parser.ParserError: while parsing a flow mapping`; the TypeError trial is
  `TypeError: float() argument must be a string or a real number, not 'NoneType'`. (The short `exception` field in
  `summary.json` is `ParserError`/`TypeError`; the qualified name comes from the traceback copy — see F2 for why that
  matters at collection time.)
- Structurally, a fifth chunk or a seventh trial cannot be admitted: `RTE_DIAGNOSED` is a four-entry literal, the
  admitted list is built only from `spec["trials"]`, and the count check requires `runtime_errors == len(declared)`.
  (The check is over-strict for the climate chunk, not over-permissive — F3.)

---

## 2. The admission path is unreachable on the real sealed records (F1, F4) — **FAIL**

The sealed stopped records are not shaped like the test fixture. They contain:

```json
"gates": {"status": "FAIL",
          "error": "STOP: 2 worker runtime_error(s); sweep-1 had none (infrastructure/worker failure)"}
```

(no `node`, no `memory_mode`, no `expected_roots`, no `worker`, no `roots`), and they have **no
`campaign_placement` key at all**. This is the code path in `run_job`: `collection_gates` raises on
`runtime_errors > 0` (`s2_c2_lib.py:793-795`); the `except Stop` sets the FAIL gates (`:955`) and
`_stop_with_evidence` re-raises (`:956`, `:662`), so `record["campaign_placement"]` (`:966`) and the successful
`finished_utc` line are never written (`finished_utc` is set by `_stop_with_evidence`; placement is not).

Therefore, in `collect_evidence`:

1. `gates = record.get("gates") or {}` → FAIL dict; `key = (None, None)` (`:1172-1173`);
2. `key not in SWEEP1_WORKER_BASELINE` → **STOP at `:1177`** — `_admitted_diagnosed_chunk` (`:1181`) is never
   reached;
3. even if that gate were bypassed, `worker = gates["worker"]` (`:1182`) would pass (synthesized), but
   `placement = record["campaign_placement"]` (`:1183`) is a **KeyError**;
4. and after all per-chunk checks, the result dict reads `record["gates"]["roots"]` / `["llm_calls"]` /
   `["parse_failures"]` (`:1228`, `:1233`, `:1234`), which do not exist on the FAIL gates → **KeyError** (F4). The
   synthesized gates are available in the `records` tuple but are not used there.

Reproduced end-to-end against read-only copies of the real sealed artifacts (all 16 records; four stopped chunks with
their `out/` and `work/` trees), `SEALED_ROOT` pointed at the copy, `collect_evidence("s2ev-20261119-a",
"4aac52092813b2b01ddb96cd7d135c390aeff645")`:

```
STOP: unexpected, stopped or duplicate chunk record:
      .../s2ev-20261119-a/openml_breast_w-append_only_summary/job_record.json
```

As a control, the same copy with only the 12 non-stopped chunks reaches the later gate
`STOP: sealed collection has 12/16 distinct node/memory pairs` — i.e. the 12 passing chunks pass all existing
gates, and only the four diagnosed chunks break the new path. The refactor therefore does not silently skip checks
for passing chunks, but it does not admit the diagnosed ones.

Directly calling `lib._admitted_diagnosed_chunk(record, digest, sealed)` for the four real records (bypassing the
unreachable gate) shows the per-trial logic also fails on real data:

```
openml_breast_w-append_only_summary       STOP: admitted trial exception differs for openml_breast_w__s145-trial-016
openml_climate-append_only_summary        STOP: admitted trial ids differ .../openml_climate__s264
openml_credit_approval-append_only_summary STOP: admitted trial exception differs for openml_credit_approval__s200-trial-011
openml_wdbc-append_only_summary           STOP: admitted trial exception differs for openml_wdbc__s150-trial-020
```

---

## 3. Per-trial verification on the real artifacts (F2, F3) — **FAIL**

**F2 — exception binding uses a string that does not occur in the sealed run log.** The unit checks
`"FAILURE_CATEGORY=runtime_error" in text and exception in text` against
`work/roots/<campaign>/art/trial-NNN/run.log` (`s2_c2_lib.py:1133-1137`). The sealed ParserError logs contain, in
full (12 lines):

```
NODE=openml_breast_w
STATUS=failed
FAILURE_CATEGORY=runtime_error
FAILURE_MESSAGE=ParserError: while parsing a flow mapping
  in "<unicode string>", line 6, column 15:
    class_weight: {0
                  ^
expected ',' or '}', but got ':'
  in "<unicode string>", line 7, column 7:
    scaler: standard
          ^
```

`yaml.parser.ParserError` is **not** a substring of that text (grep over the whole chunk tree finds it nowhere; the
only occurrence is in the committed diagnosis `traceback.txt`, which is a replay copy under `/tmp`, not sealed
evidence). Hence all five ParserError trials can never verify; only the TypeError trial could, and its chunk is
still blocked by the other trial. A reviewer should not accept a binding whose literal string is absent from the
evidence it is bound to; the declaration should either use the exact sealed text (e.g. match the `FAILURE_MESSAGE=`
line's `ParserError: while parsing a flow mapping`) or bind the committed diagnosis traceback by hash — not silently
rely on "exact exception" while checking a different artifact.

**F3 — two diagnosed trials in one campaign root.** `openml_climate__s264` has both
`openml_climate__s264-trial-019` and `openml_climate__s264-trial-020` as `failure_category: "runtime_error"` rows in
the same `root_trials.jsonl` (verified in the sealed `work/roots/openml_climate__s264/root_trials.jsonl`). The loop
for the first declared trial computes `errors` = both rows and requires
`[row["trial_id"] for row in errors] == [trial_id]` (`:1131-1132`) — an exact one-element list — so both iterations
fail. The rule must be set-equality between the declared per-campaign subset and the campaign's runtime-error rows,
not "exactly one row".

Other observations on the verification logic (after the blockers are fixed):

- Record mutation is genuinely pinned: the raw-bytes SHA-256 of `job_record.json` is checked against both the
  declared constant and the sealed `SHA256SUMS` line; `stop`, `label`, `finished_utc`, `chunk_id` are checked.
- Extra/missing trials are structurally covered once reachable (per-campaign row set, `runtime_errors == len`,
  `successful + failures == trials`), but this is exactly the rule that is wrong for same-campaign trials.
- **F6 (evidence-binding gap, hardening):** `collect_evidence` verifies the hash only of `job_record.json`. The new
  unit then trusts `out/collection_checks.json`, `out/worker_failure.json`, `work/roots/*/root_trials.jsonl` and
  `art/*/run.log` without checking their sealed `SHA256SUMS` lines, although `seal()` wrote them (977–1013 hashes per
  chunk; I re-verified all lines OK). The record hash must be accompanied by hash verification of every artifact the
  admission reads; otherwise the admission's evidence is not cryptographically bound to the reviewed seal.
- Exception matching is a plain substring anywhere in the log (not anchored to the `FAILURE_MESSAGE=` line). Once
  the string is corrected, anchor it to the line to avoid accidental matches from traceback text.
- Missing/corrupt admission artifacts raise `FileNotFoundError`/`JSONDecodeError` (not `Stop`) and abort with a
  traceback rather than a clean collection STOP; fail-closed but an inconsistent failure mode. `budget_index: null`
  would raise `TypeError` at `int(index)`.
- No route to an extra root: the outer `len(roots) != 18`, `placement.keys() != roots.keys()`,
  `expected_roots == 18`, `root_failures == 0` checks are retained for chunks whose admission path is reached.

---

## 4. Collect-gate paths — **partially preserved, but the refactor breaks the stopped-chunk path**

What is still enforced for every chunk that reaches the checks (verified by reading the refactor and by the 12-chunk
control run): 16 distinct `(node, memory_mode)` pairs (`:1214-1215`), frozen image + GPU ≥24 GB + CC ≥7.0 +
placement/identity equality (`:1184-1201`), 18 roots/expected_roots/root_failures/one success per root
(`:1202-1209`), `llm_calls > 0` and parse-failure rate ≤20% (`:1207-1208`), pooled failure-rate margin
(`:1217-1223`). The `records` tuple/loops were updated consistently except for the four stale `record["gates"]`
reads listed in section 2 (they only fail for stopped/admitted chunks).

Changes to STOP paths are limited to the intended one: the old reject condition included `record.get("stop")`
(rejecting all stopped chunks with "unexpected, stopped or duplicate"); it is removed so `stop` records route into
`_admitted_diagnosed_chunk`, which stops every record not exactly matching the declared (chunk, digest, stop, label)
tuple. Chunk-time gate (`chunk_wall_s > walltime`), collection-gates STOPs, and every other STOP are untouched. No
threshold constant was changed (`SWEEP1_WORKER_BASELINE`, `WORKER_FAILURE_MARGIN`, `MAX_PARSE_FAILURE_RATE`,
`WORKER_BINOMIAL_ALPHA` unchanged in the diff).

---

## 5. Accounting — design correct, but unreachable (F4)

Intended accounting (if the admission path worked) is right: the synthesized `worker` (`s2_c2_lib.py:1147-1157`) sets
`runtime_errors = 0`, removes the `runtime_error` category, adds `len(declared)` to `invalid_config`, and adds
`admitted_diagnosed_runtime_errors`; `worker["failures"]` and `["trials"]` are unchanged, so the six admitted
trials remain counted as **failures** (both in the chunk gate and in `worker_failures` of the result) and the pooled
margin `failures / trials <= sweep1 + 5 pp` still applies. `admitted_diagnosed_records` is added to the result as
required (`:1236`). The four stopped chunks' real checks confirm the arithmetic: e.g. breast
`trials 360, successful 272, failures 88, runtime_errors 2, {invalid_config: 86, runtime_error: 2}` → synthesized
`{invalid_config: 88, runtime_error absent, runtime_errors: 0}` with failures still 88.

What breaks it is F4 (result reads `record["gates"]` instead of the synthesized gates) and F1 (never reached), so
`collection_counts.json` would not be produced correctly. There is no change to the chunk-time gate or to any other
STOP; `admitted_diagnosed_records` is the only new result field.

---

## 6. Tests — 4 pass, but coverage does not exercise the real shape

- `pytest r1/tests/htcondor/test_s2_rte_admit.py -q -p no:cacheprovider` → **4 passed** (1 happy path + 3
  reject-parametrisations: wrong digest, wrong trial id, wrong exception class).
- `pytest r1/tests/htcondor -q -p no:cacheprovider`:
  - branch `a5d06f58`: **570 passed, 1 skipped** (8.76 s) — i.e. base 566 + 4 new, no regression;
  - clean base `d47d1008` (`/private/tmp/base_d47`): **566 passed, 1 skipped**; `test_g1b_h200.py` on base:
    **101 passed, 1 skipped**. In this environment I could **not** reproduce the 4 pre-existing
    `test_g1b_h200.py` failures noted in the review brief; the base is green and the branch adds only the 4 new
    passes, so either way there is no regression from this unit. (The brief's 4 failures may be host/data-specific
    — e.g. a checkout with different evidence files — but they are not present at clean `d47d1008` here.)

Coverage assessment: the added tests only call `_admitted_diagnosed_chunk` with a fabricated record
(`{"chunk_id","stop","finished_utc","label"}`) and a fabricated sealed tree with **one** runtime-error trial per
campaign and a plain `FAILURE_MESSAGE=ParserError: bad yaml`; they never call `collect_evidence`. They therefore
cannot catch: F1 (real FAIL gates / no `campaign_placement`), F4 (stale `record["gates"]` in the result), F2
(qualified exception absent from `run.log`), F3 (same-campaign second trial), missing/extra artifacts, count
inconsistencies, or a fifth chunk/seventh trial. Fail-closed cases covered are only digest/trial/exception on the
synthetic tree. At minimum an integration test over a **real-shaped** sealed directory (FAIL gates, no
`campaign_placement`, two same-campaign runtime-error rows, `yaml.parser.ParserError`-style traceback in `run.log`,
plus a passing chunk) is needed before this unit can be trusted.

---

## 7. Disclosure, thresholds, sealed originals

- **Disclosure:** the governing row `docs/r1/PLAN.md:1349` @ `d47d1008` says the four chunks are accepted "through a
  reviewed collection change that admits exactly these six diagnosed records; disclosed in the sweep-2 report", and
  amends the "any runtime_error is a STOP" rule "for exactly these six records under (i)". This diff adds **no**
  report/disclosure text (only code + tests; no sweep-2 results report exists on the branch yet), so the disclosure
  obligation is not yet discharged in this change — it must appear in the sweep-2 report when the collection result
  is written. If the unit were accepted, the report would have to say the six are admitted only through this
  reviewed unit (and, after the fixes above, through the sealed-artifact checks).
- **No threshold relaxation beyond the six:** confirmed. No gate constant changed; the only STOP relaxation is the
  per-record admission path, which (as written) admits nothing and therefore cannot be a hidden relaxation.
- **Sealed originals untouched:** verified. On `deepthought.etp.kit.edu` I recomputed every line of the four chunks'
  `SHA256SUMS` (977 / 1013 / 977 / 977 lines): **0 mismatches**; each sealed `job_record.json` byte hash equals the
  declared constant and its `SHA256SUMS` line; the six trial ids/config values/tracebacks match the committed
  diagnosis. All access was read-only; the local probes used copies under `/private/tmp`.

---

## 8. Required before acceptance

1. Do not take `node`/`memory_mode` from the record's `gates` for stopped chunks (they are the FAIL dict); read them
   from the sealed `out/collection_checks.json` (already needed) or synthesize gates before the key check, and stop
   cleanly if they disagree with `SWEEP1_WORKER_BASELINE`.
2. Do not read `record["campaign_placement"]` for stopped chunks (absent). Build the placement check from the record's
   `site`/`gpu`/`cpu`/`collector` fields (or from `checks`), then run the same image/GPU/placement/root checks.
3. Fix the exception binding: use text that actually occurs in the sealed `run.log`
   (`FAILURE_MESSAGE=ParserError: while parsing a flow mapping` for the five; `TypeError: …` for the one), anchored to
   the `FAILURE_MESSAGE=` line; or bind the committed diagnosis traceback by hash. Do not claim an "exact exception"
   that is absent from the artifact being checked.
4. Per-campaign trial rule: compare the **set** of declared trials for a campaign against the set of
   `runtime_error` rows in that campaign's `root_trials.jsonl` (climate has two), and require every declared trial
   to be present, no extras, and the count check to equal the declared total.
5. In the result block use the synthesized gates (from the `records` tuple) for `campaigns`, `llm_calls`,
   `parse_failures` rather than `record["gates"]` (F4).
6. Verify the sealed `SHA256SUMS` lines for every `out/`/`work/` artifact the admission opens; keep the record hash
   check.
7. Add the integration/real-shaped tests described in section 6; re-run `r1/tests/htcondor` (570 passed, 1 skipped
   baseline for this branch) and, before recording acceptance, demonstrate that `collect_evidence` on a copy of the
   real sealed run reaches `16/16` chunks, returns the six `admitted_diagnosed_records`, keeps failure totals and the
   pooled-margin verdict, and leaves `runtime_errors: 0` in the synthesized chunk gates.

---

**VERDICT: NOT ACCEPTED**

---

# Round 2 — independent re-review (tip `1695ac44`)

**Reviewer role:** same fresh, independent, read-only reviewer. **No job, server, collection run on the real tree or
`condor_*` command was started; no git write was made.** This round-2 section is appended uncommitted to the round-1
file (the author committed the round-1 file in `1695ac44`; the round-1 text above is unchanged). Sealed chunks were
read only (read-only SSH; `sha256sum`-style re-verification; local probes on copies under `/private/tmp/rte_r2.*`,
never written back).

**Date/time:** 21 November 2026, 11:37–12:10 CET.

**Unit under review:** branch `s2-rte-admit-20261121` @ **`1695ac44`** (single fix commit; parent `a5d06f58`, base
`d47d1008`; worktree clean except this appended section). Diagnosis branch unchanged at `342b06eb`; sealed run
`s2ev-20261119-a` / commit `4aac5209`.

| file | lines | SHA-256 |
|---|---:|---|
| `sweep2/s2_c2_lib.py` @ `1695ac44` | 1302 | `12e160f686ea9ee27ad44fd6e88ce41edc5e7f4f64888c39f0f7854bb08bfb22` |
| `r1/tests/htcondor/test_s2_rte_admit.py` @ `1695ac44` | 75 | `f7d2c99d8fc23d4bba8e306a25669cdd87ee3f6f6ade0d652a4c941167116979` |
| `docs/r1/reviews/S2_RTE_ADMIT_REVIEW_20261121.md` @ `1695ac44` (round-1) | 302 | `090572488204fc288200984a5134e7ca83dbceedab1752503867a501c46f7368` |

Diff `a5d06f58..1695ac44`: 3 files, +403/−64 — `sweep2/s2_c2_lib.py` (+102/−64), the test file (+63/−12), and the
committed round-1 review (+302). Nothing else changed; no threshold constant touched; chunk-time gate and all other
STOPs untouched.

**Round-2 verdict: ACCEPTED.** All four round-1 blockers are fixed and independently reproduced on the real sealed
data; the end-to-end collection on a read-only copy of the real run now passes with the six admitted records and the
accounting required by the R1-SWEEP2-RTE-DIAG row. Residual items below are non-blocking.

---

## R2.1 Round-1 findings mapped to the fix

- **F1 (record shape) — fixed.** For a record with `stop`, `_admitted_diagnosed_chunk` now derives the key from the
  sealed `out/collection_checks.json` (`s2_c2_lib.py:1133`) instead of the FAIL `record["gates"]`, and validates it
  against `SWEEP1_WORKER_BASELINE` plus the chunk-id suffix/prefix
  (`:1134-1143`). `collect_evidence` routes stopped records through admission *before* the reject gate, so the
  `(None, None)` key path is gone (`:1192-1197`). Stopped records indeed have no `campaign_placement`; the loop now
  synthesizes `{root: {} for root in worker["roots"]}` (`:1203-1205`) and skips only the per-row placement equality
  for admitted chunks (`:1220`), while the site/host/GPU/CPU presence, frozen image, GPU model/VRAM/CC, 18-root and
  root-keys checks still run for them. Normal chunks keep the full placement equality. This is sound: the admitted
  record has no sealed placement to compare against, while the root set comes from the hash-bound checks artifact and
  the node/memory pair from the chunk id.
- **F2 (exception text) — fixed.** The declared exceptions are now the sealed-log tokens `ParserError` (5) and
  `TypeError` (1), matching the diagnosis `summary.json` `exception` field, and are matched as
  `FAILURE_MESSAGE=<exception>:` together with `FAILURE_CATEGORY=runtime_error` in the sealed `run.log`
  (`:1148-1158`). The qualified `yaml.parser.ParserError` remains in the committed diagnosis traceback; the sealed
  log only ever contained `ParserError: …`, so this is the correct artifact-level binding.
- **F3 (two trials in one climate campaign) — fixed.** Declared trials are grouped by campaign into sets (`:1138-1144`)
  and each campaign's runtime-error rows are compared by set equality, plus an explicit `len(errors) ==
  len(trial_ids)` duplicate guard (`:1146`); climate t019 and t020 now both admit, while extra/missing rows still STOP.
- **F4 (stale gates in result) — fixed.** Result assembly uses `gates_list` for `campaigns`, `llm_calls`,
  `parse_failures` (`:1239`, `:1250-1254`), i.e. the synthesized gates for admitted chunks.
- **Secondary — fixed.** Every artifact the admission opens (`out/collection_checks.json`,
  `out/worker_failure.json`, each `root_trials.jsonl`, each `run.log`) is read through `artifact()` and checked
  against its exact sealed `SHA256SUMS` line (`:1122-1130`); the `job_record.json` hash check is unchanged. The
  exception match is anchored on the `FAILURE_MESSAGE=` prefix.

Residual code observations (non-blocking, see R2.6): missing/corrupt admission artifacts still surface as uncaught
`FileNotFoundError`/`JSONDecodeError` (fail-closed — no admission, no counts written — but a traceback rather than a
clean `Stop`); the sealed `SHA256SUMS` is itself not externally pinned; the per-row placement equality is
deliberately skipped for admitted chunks (justified above).

## R2.2 Independent verification on the real sealed data

**Sealed originals still untouched.** Read-only SSH re-check of all four chunks' `SHA256SUMS` after the author's
end-to-end claim: 977 / 1013 / 977 / 977 lines, **0 mismatches**. The real `/ceph/srv/dwong/paperb/sweep2/
s2ev-20261119-a/` tree has no `collection_counts.json` and no new files; the four sealed `job_record.json` hashes
still equal the code constants and their `SHA256SUMS` lines. The diagnosis/trial binding is unchanged (6 = 6, no
extra/missing; chunk/campaign/trial ids and `ParserError`/`TypeError` match `summary.json`).

**End-to-end `collect_evidence` PASS on a fresh copy of the real run.** I copied the real sealed artifacts read-only
(the four stopped chunks with full `out/`+`work/`, plus `job_record.json`+`SHA256SUMS` for all 16 chunks — exactly
what the code opens), pointed `SEALED_ROOT` at the copy, and ran
`collect_evidence("s2ev-20261119-a", "4aac52092813b2b01ddb96cd7d135c390aeff645")` on round-2 code:

| result field | value |
|---|---|
| chunks / live_nodes / campaigns | 16 / 8 / 288 |
| worker_trials / worker_failures | 5760 / 460 |
| sweep1 trials / failures | 5760 / 473 |
| worker_failure_rate / limit | 0.079861… / 0.132118… |
| llm_calls / parse_failures | 5796 / 0 |
| gpu_models / status | `NVIDIA H200` / `PASS` |
| `admitted_diagnosed_records` | 6 (breast s145-t016, s155-t019; climate s264-t019, t020; credit s200-t011; wdbc s150-t020) |
| `chunk_record_sha256` | 16 entries, all equal to the sealed record hashes |
| `collection_counts.json` | written (`schema: s2_collection_counts/1`) |

I independently recomputed the raw totals from the 16 sealed records/checks: trials 5760, failures 460,
runtime_errors 6, llm_calls 5796, parse_failures 0 — **the admitted six remain counted as failures, so the failure
totals and the pooled margin verdict are unchanged** (`460/5760 = 7.99 %` vs the `473/5760 + 5 pp = 13.21 %` limit).
The synthesized per-chunk workers are `runtime_errors: 0` with the two/one runtime errors moved into
`invalid_config` (`openml_breast_w` 86→88, `openml_climate` 82→84, `openml_credit_approval` 70→71,
`openml_wdbc` 67→68); failures/trials unchanged (88/84/71/68 of 360). The 12 non-diagnosed chunks are unchanged
(control: with only those 12, the run reaches the expected "12/16 distinct node/memory pairs" STOP).

**Tests.** `r1/tests/htcondor/test_s2_rte_admit.py` → **6 passed**; full `r1/tests/htcondor` → **572 passed, 1 skipped**
(8.14 s) vs clean base `d47d1008` **566 passed, 1 skipped** (7.97 s) — base + 6 new, no regression. (As in round 1,
the brief's 4 pre-existing `test_g1b_h200.py` failures are not reproducible at clean `d47d1008` in this environment;
the base file is 101 passed, 1 skipped here. Either way the branch introduces no failure.)

## R2.3 Fail-closed behaviour — probed on the real sealed copies

Each probe used a fresh copy of the real 16-chunk tree, one mutation, then `collect_evidence`; none admitted
anything and none wrote `collection_counts.json` (the only writes were the pre-created-file probe below):

| scenario (real-data copy) | observed |
|---|---|
| mutate `out/collection_checks.json`, sums not updated | `Stop: admitted chunk artifact is not bound by the sealed SHA256SUMS` |
| remove the `out/worker_failure.json` line from `SHA256SUMS` | same `Stop` (artifact not bound) |
| mutate a sealed `run.log`, sums not updated | same `Stop` (artifact not bound) |
| mutate `job_record.json`, sums not updated | `Stop: sealed record hash differs` |
| re-point `checks.node` to another valid pair + update sums | `Stop: admitted chunk does not identify one of the 16 fixed node/memory pairs` |
| add a 7th runtime_error row in `openml_climate__s264` + update sums | `Stop: admitted trial ids differ …` |
| remove the declared climate t020 runtime_error row + update sums | `Stop: admitted trial ids differ …` |
| change a declared `run.log` `FAILURE_MESSAGE=` to another exception + update sums | `Stop: admitted trial exception differs` |
| delete a declared `run.log` | `FileNotFoundError` (uncaught; fail-closed, no counts) |
| corrupt `out/worker_failure.json` + update sums | `JSONDecodeError` (uncaught; fail-closed, no counts) |
| change a stopped record's `stop` + update sums (digest ≠ declared) | `Stop: stopped chunk is not one of the six diagnosed …` |
| give a passing chunk a `stop` + update sums (undeclared stop) | `Stop: stopped chunk is not one of the six diagnosed …` |
| declare a 7th trial via in-memory `RTE_DIAGNOSED` edit | `Stop: admitted trial ids differ …` (no admission) |
| duplicate a chunk's (node,mode) pair under a new chunk id | `Stop: unexpected, stopped or duplicate chunk record` |
| add a 19th root to `checks.worker.roots` + update sums | `Stop: collection or worker gate failed` |
| missing chunk `SHA256SUMS` | `FileNotFoundError` (fail-closed) |
| pre-existing `collection_counts.json` | `FileExistsError` (no overwrite; fail-closed) |

This covers the round-1 bypass list: declared trial absent/extra, seventh trial, fifth chunk (structurally excluded
by the four-entry literal; an undeclared stopped chunk is rejected), exception-text substitution, record mutation,
duplicate chunks/pairs, missing artifacts and extra roots. All paths fail closed; the uncaught-exception cases abort
with a traceback instead of a clean `Stop` but still prevent admission and `collection_counts.json`.

## R2.4 Test-coverage assessment (improved, still unit-level)

The six tests now use real-shaped records (no `gates`, no `campaign_placement`, SHA256SUMS-bound artifacts) and cover
happy-path admission plus rejections for wrong digest, wrong trial id, wrong exception, artifact-hash tamper, and
chunk/node mismatch. Remaining gaps (recommended, non-blocking): (a) **no test for two declared trials in one
campaign** — the F3 regression is untested even though `_sealed()` accepts a `trials` tuple (it would write the same
campaign's `root_trials.jsonl` twice, so it needs a small aggregation change first); (b) **no `collect_evidence`
integration test** — the round-1 blockers were precisely integration-shape bugs, and the end-to-end run remains a
manual/author-only check in the suite; (c) not covered: extra/undeclared runtime_error rows, undeclared stopped
chunks, duplicate pairs, missing/corrupt artifacts, and the uncaught-exception failure mode. My independent
end-to-end and the R2.3 probes cover these today, but a regression test for F3 and a synthetic 16-chunk
`collect_evidence` test would protect them in future.

## R2.5 Accounting, thresholds, disclosure

- Accounting verified above: six admitted as failures, `runtime_errors` 0 in synthesized gates, failure totals and
  pooled margin unchanged, `admitted_diagnosed_records` present, 12 normal chunks unchanged.
- **No threshold relaxation beyond the six:** no gate constant changed (`SWEEP1_WORKER_BASELINE`,
  `WORKER_FAILURE_MARGIN`, `WORKER_BINOMIAL_ALPHA`, `MAX_PARSE_FAILURE_RATE`, `FROZEN_IMAGE`, GPU limits all
  untouched); the only STOP-path change is the intended per-record admission routing; the chunk-time gate and the
  other collection STOPs are unchanged.
- **Disclosure:** the `docs/r1/PLAN.md:1349` row still requires that the six be admitted "through a reviewed
  collection change … disclosed in the sweep-2 report". No sweep-2 results report exists yet, so the disclosure
  remains an obligation for that report when the collection result is written; this branch now (unlike round 1)
  actually produces such a result.
- **Sealed originals:** untouched (verified after the author's end-to-end run; only read-only access from this
  review).

## R2.6 Residual follow-ups (non-blocking)

1. Add the missing tests from R2.4, in particular a two-trials-one-campaign case and a synthetic 16-chunk
   `collect_evidence` integration test.
2. Optionally wrap artifact read/`json.loads` failures in `Stop` so a damaged sealed tree yields the reviewed STOP
   message rather than a traceback (currently fail-closed either way).
3. The admission's evidence chain terminates at the sealed `SHA256SUMS`, which is not externally pinned; if the
   review standard requires cryptographic binding beyond "the sealed tree is trusted", commit a digest of each
   chunk's `SHA256SUMS`/`SEAL_RECEIPT.json` in the unit or the sweep-2 report.
4. `ParserError`/`TypeError` now bind the sealed-log token; the qualified `yaml.parser.ParserError` is evidenced only
   in the committed diagnosis traceback. This matches the diagnosis `summary.json` and is acceptable; if an "exact
   qualified class" is desired later, bind the committed traceback artifact by hash too.

---

**Round-2 verdict: ACCEPTED** — all four round-1 blockers are resolved and independently verified on the real
sealed data; the end-to-end collection gives 16 chunks / 5,760 trials / 460 failures (7.99 % vs 13.21 %) with the six
diagnosed records admitted and accounted as `invalid_config`, and every probed deviation fails closed.

VERDICT: ACCEPTED
