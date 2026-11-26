Reviewed base: origin/main `912a7e027`; accepted at `30c584def` (branch `mac-xc3-short-crosscheck-20261125b`), post-acceptance fixes confirmed at `b14cb887b7ce05ae4374cdbf66236b89778f4993` (branch `mac-xc3-short-crosscheck-20261125c`; launch commit `6f4e2ba1ed6cc85c61f1eecdae08ed40db8c6a42`)

# Independent review record — xc3: the short cross-host check for mlab_imdb, mlab_ogbn_arxiv, mlgym_fmnist and mlgym_houseprice (R1-G5-AUDIT-TWO-CARDS), its note draft and launch commit

**Unit.** `sweep2/t1_tasl/g1b_crosscheck.py` (schema `g1b_tasl_crosscheck_short_spec/1`, `compare --mode short`, `check-xc-note --draft`,
`verdict-status`, `short_cap_gate`), the spec `sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json` (run `g1b-tasl-20261121-b-xc3-a`), the builder
`sweep2/t1_tasl/build_xc3_launch.py` and its config, the note draft `docs/r1/proposals/G1B_XC3_SHORT_NOTE_DRAFT_20261125.md` (`approved: false`),
tests `r1/tests/test_t1_tasl_crosscheck.py` and `r1/tests/test_t1_tasl_xc3.py`, and the report
`docs/r1/reports/tasl_chain_20261122/XC3_SHORT_CROSSCHECK_PREP_20261125.md`. Authority: R1-G5-AUDIT-TWO-CARDS, R1-T1-D21-SCOPE, R1-G1B-CAP,
R1-G1B-JOIN; the queue of 25 Nov 2026 (12:00), item 2(c).

**Process.** One independent reviewer for all rounds, read-only, no label, evaluation, sealed or secrets file opened, scratch moved to its
`_to_delete/`. Round 1 found that three of the four TASL-2 `job_record_sha256` pins were the sha256 of `SHA256SUMS` (blocking) and that
signing the note unchanged silently adopted the XC3-FAIL and cap recommendations (major). The author rebuilt the unit on a new branch
(`…-20261125b`; the first branch `mac-xc3-short-crosscheck-20261125` at `f45f2359` is superseded and not for merging); round 2 accepted it with
three minors and two nits, which were fixed in one more rebuild (`…-20261125c`), confirmed by the same reviewer, who reproduced the launch
commit `6f4e2ba1` from the builder in a scratch clone.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `912a7e02` 58 failed, 3972 passed, 197 skipped, 3 errors;
build tip `55f23299` 58 failed, 4026 passed, 197 skipped, 3 errors; the failure lists `FULLSUITE_XC3_BASE_912a7e02.txt` and
`FULLSUITE_XC3_TIP.txt` are identical (61 lines; node ids equal to the standard list once pytest's message suffix is cut).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `f45f2359` | NOT ACCEPTED (BLOCKING 1 pins; MAJOR 2 signing; minors 3–6) |
| 2 | `30c584de` | ACCEPTED (three minors, two nits) |
| 3 | `b14cb887` | CONFIRMED (all six items fixed; launch commit reproduced) |

**Open items for the author** (report §8): XC3-FAIL (A: a non-PASS keeps the node's audits off TASL-7 only; B: the literal reading of
R1-T1-D21-SCOPE, the node leaves G.5), proposed as PLAN row R1-XC3-FAIL-READING and mirrored in the note's `xc3_fail` line; XC3-CAP
(2.0 GPU-h inside R1-G1B-CAP or G5-CAP); `skip_nodes` (whether to skip mlgym_houseprice); the signature. Before the run: copy the house-price
CSV to TASL-7; TASL-7 has no recorded data manifest for mlab_imdb and mlab_ogbn_arxiv.

## Round 1 (`f45f2359`)

> **Round 1, `f45f2359`: NOT ACCEPTED.** The design is sound and the PASS criterion is unchanged, but three of the four TASL-2 pins point at the wrong file.
>
> ### BLOCKING 1: three `job_record_sha256` pins are the sha256 of `SHA256SUMS`, not of `job_record.json`
> - Where: `sweep2/t1_tasl/g1b_crosscheck_xc3_spec.json:16,19,25` (template in `b7933583`, base `0d561485`), note draft `:34`, `r1/tests/test_t1_tasl_xc3.py:41-44`, launch table, prep report §5.
> - Evidence: `AR_G1B_TASL2_RESULT_20261122_captures/inputs/baseline_initial_state.txt:116,121,131` and `G1B_TASL2_FMNIST_AMENDMENT_20261122_captures/inputs/untouched_confirmed.txt:17-50` list `8415daa8…`, `88677a1a…`, `0109ecc2…` against `…/attempt-1/SHA256SUMS`. The `job_record.json` lines give mlab_imdb `4468021ac41507b4a9161746e8f178d0ae98c938e18e3b91167d1d806d3c4eae`, mlab_ogbn_arxiv `45583b2717b1b0817c4e2c1e5cec7202a47b718b4ffd4d52e71dc66b249c0cac`, mlgym_houseprice `15b7beea61f7829d396a9aa0415462e80c3aabd6c62c9c3327b2528af2a690aa`. Confirmed by reconstructing each `SHA256SUMS` (same method gives fmnist's recorded `dc0687f5…`). The fmnist pin (attempt 3, `5476148a…`) is correct.
> - Effect: `compare --mode short` (`g1b_crosscheck.py:417-422`) refuses the TASL-2 side of three nodes after their TASL-7 jobs ran (≈0.78 GPU-h + 2.1 CPU core-h wasted); they can never PASS. Fails closed.
> - Tests missed it: `test_t1_tasl_xc3.py:97` only checks the hash appears somewhere in the capture.
> - Fix: correct the pins on a new base; rebuild the launch commit, note `xc_spec_sha256` and table; make the test require the capture path to end in `/<node>/attempt-N/job_record.json`; optionally pin `SHA256SUMS` too.
>
> ### MAJOR 2: XC3-FAIL / XC3-CAP and the signing procedure
> - Signing as instructed (only `approved` and P4) silently adopts XC3-FAIL A and XC3-CAP inside R1-G1B-CAP; nothing tells the author how to record B; `check_xc_note` strict does not bind those lines.
> - XC3-FAIL decides the reading of R1-T1-D21-SCOPE (C3's node set): a PLAN-level decision (precedent R1-G1B-JOIN). The literal reading B is stronger than shown: R1-G5-AUDIT-TWO-CARDS itself calls the short check "a cross-host check PASS for that node".
> - houseprice deserves its own line: most likely to fail (CPU bits across two CPUs), D21-qualifying, CPU-only audits gain little from TASL-7; under B its voluntary check risks dropping it.
> - Fix: state that signing unchanged adopts the recommendations and name the lines to edit otherwise (and whether re-review is needed), or record XC3-FAIL/XC3-CAP as author rows before signature; add the AUDIT-TWO-CARDS wording and the houseprice consequence to `g5_entry`.
>
> ### minor 3: code version on each side not stated (TASL-2 ran `10fd3343` / `3c3f822a`; TASL-7 runs `0d561485`); the relevant files are unchanged (checked) — add one sentence.
> ### minor 4: nothing enforces the 2.0 GPU-h cap during the run; worst case ≈7.1 GPU-h of lease time; state it and add a stop rule between GPU jobs.
> ### minor 5: a houseprice mismatch cannot be attributed: add `lscpu` and numpy/scipy BLAS info (threadpoolctl) captures on both hosts. (STOP `cross_host_mismatch` is correctly not an infrastructure STOP and never a PASS.)
> ### minor 6: `verdict-status` (`g1b_crosscheck.py:699-733`) fails closed but should check `complete is True`, all rows `identical`, both sides deterministic for a PASS, and raise if `origin/main` does not resolve.
> ### nits: the launch-commit sha reproduces only with the same SSH signing key (say so in the builder docstring); cpus 8-15 on a 7900X may share cores with 0-3 (timing only); `test_t1_g5_tasl` 116 not 115; prep report header names `5d4f1b09` as base.
>
> ### What checked out
> "Short" is the reviewed preassembly comparison with hosts swapped (same harness `c025f89a`, node entries identical in `060aac91`/`7ff3c95b`, freeze and manifest enforced at job start, borrowed `extra_env` safe). `compare` adds only the short-side pin check, `on_stop` text and rule; xc2 spec `a9e6b463…` and derived specs byte-identical; six xc2 bindings recomputed. Launch commit rebuilt in a scratch clone: same `dc5c2c12`, tail `a50d0063`, table `339cfd59`; only the spec outside docs/; `paper.commit` = parent `0d561485`, which merges `912a7e02`. `validate`, `check-xc-note --draft` ok; `verdict-status` PENDING ×4. Note arithmetic correct (1.039/1.184 GPU-h; 2.112/2.169 core-h; 40 runs). Tests: crosscheck 64, xc3 5, g1b 45, chain 16, g5_tasl 116, g1b_ar 69 passed; full-suite lists byte-identical (61 lines). Autoresearch excluded; no G.5 code or PLAN change; no `approved: true`.

## Round 2 (`30c584de`)

> **Round 2, branch `mac-xc3-short-crosscheck-20261125b` @ `30c584de`: ACCEPTED.** BLOCKING 1 and MAJOR 2 are fixed; the whole rebuilt branch was re-reviewed. Remaining items are minor or nits.
>
> ### Checks
> - Pins verified independently against `AR_G1B_TASL2_RESULT_20261122_captures/inputs/baseline_initial_state.txt` at the exact paths `sealed_g1b/g1b-tasl-20261121-b/<node>/attempt-N/<file>`: `job_record.json` `4468021a…`, `45583b27…`, `5476148a…`, `15b7beea…`; `out.tar` `0faf572d…`, `04f2d0c7…`, `a180c6e5…`, `2588cd30…`; `SHA256SUMS` `8415daa8…`, `88677a1a…`, `dc0687f5…`, `0109ecc2…`; each SHA256SUMS pin equals the file rebuilt from the other two; fmnist also equals the amendment's sealed copy. `validate` recomputes the consistency; `compare --mode short` checks both pins; the build test requires the exact path.
> - Launch commit rebuilt in a scratch clone (base `1af85477`, `wip-xc3b-tail` `04150dcf`): `9d47549c`, tail `d60d1f5d`, table `c77c831c` reproduce (same SSH key; docstring says so). The launch commit changes only the spec (`805a9b96…`) and the note; `paper.commit` `1af85477` sits directly on `912a7e02`.
> - xc2 unchanged: spec `a9e6b463…`; `g1b_tasl.py`, `g1b_lib`, `t1_tasl_node.sh`, `g1b_tasl_join.py`, `g5_tasl.py`, `build_launch_chain.py`, PLAN.md and authorizations byte-identical to main; `g1b_crosscheck.py` changes only in short-only paths; the six xc2 bindings test passes; no test line removed.
> - Desk: `validate` ok (1.039/1.184 GPU-h; 2.112 core-h; 0.428/0.266/0.345 per node); `check-xc-note --draft` ok; `verdict-status` PENDING ×4.
> - Tests one file at a time: crosscheck 76, xc3 5, g1b 45, chain 16, g5_tasl 116, g1b_ar 69 passed; full-suite lists byte-identical (61 lines).
> - `short_cap_gate`: sums started→finished hours per GPU attempt, adds the next projection, refuses above 2.0 (1.74 + 0.345 refused; 1.5 + 0.345 allowed); CPU node adds nothing; worst case ≈7.1 GPU-h without, ≤≈4.1 with the rule; fails closed on missing or unreadable records.
> - Note key lines `xc3_fail` (A|B), `xc3_cap` (R1-G1B-CAP|G5-CAP), `skip_nodes` (none or proper subset) enforced in draft and strict; refusals tested; `launch_xc` refuses a skipped node; signing-unchanged text explicit; B presented fairly; houseprice line; §8 proposes R1-XC3-FAIL-READING.
> - Minors 3, 5, 6 addressed. Scope: no G.5 code, PLAN or authorizations change; no `approved: true`; autoresearch excluded.
>
> ### Remaining (none blocking)
> - minor: `short_consumed_gpu_hours` accepts a negative attempt duration, lowering the hours used (−1.0 h took 1.74 to 0.74): the one fail-open path. Refuse `hours < 0`.
> - minor, cross-unit: a capture keeping a copy named `G1B_XC3_SHORT_VERDICT_<node>_<date>.json` under `docs/r1/reports/…_captures/` would trip G.5's near-miss rule; forbid such copies or have G.5 match only the bound paths.
> - minor, cross-unit: the PLAN row and the `xc3_fail` line agree only in prose; whichever G.5 reads, check the other.
> - nit: note header names the old branch.
> - nit: the note's `comparison` line omits the SHA256SUMS pin.
>
> ### For the G.5 reader
> Note path `docs/r1/authorizations/g1b_xc_short_t1_tasl_<YYYYMMDD>.md` (date chosen at signature); require exactly one on `origin/main`; validate with `X.check_xc_note` strict against spec `805a9b96…`; read `X.short_decisions(fields, xc)["xc3_fail"]`. Format: one line `xc3_fail: A` or `xc3_fail: B` (draft line 62; `xc3_cap` 63; `skip_nodes` 64); parser `^([A-Za-z0-9_]+)\s*:\s*(.*)$`, duplicates refused, case-sensitive. xc3 creates no other `.json` with the `G1B_XC3_SHORT_VERDICT_` prefix.

## Round 3 (`b14cb887`)

> **Confirmation round: CONFIRMED.** Branch `mac-xc3-short-crosscheck-20261125c`, tip `b14cb887`.
>
> 1. Changes from 20261125b (`30c584de`) to 20261125c (`b14cb887`) are only the six round-2 items plus regenerated shas: `short_consumed_gpu_hours` refuses `hours < 0`; `verdict-status` lists `docs/r1/reports/` on origin/main (`_list_main_reports`) and refuses any `G1B_XC3_SHORT_VERDICT_*` other than the four bound paths, and refuses if the listing fails; strict `check_xc_note` reads PLAN on main via `xc3_fail_row_option` (row once, exactly one sentence, must match the note; draft mode reads nothing; `launch_xc` passes `read_main`); helper docstrings; note header, `comparison` line (SHA256SUMS pin), `publication` line (`captured_verdict_<node>.json`), PLAN-row sentence, `paper_commit` `59fbd7d3`, `xc_spec_sha256` `fc064ded…`; spec changes only in `paper.commit`; builder config updated, builder unchanged; three new tests, none removed.
> 2. Rebuild in a scratch clone from base `59fbd7d3` with `wip-xc3c-tail` `ad2cf928` reproduces launch commit `6f4e2ba1`, tail `8b0bd89b`, table `55f23299` (tree identical); the launch commit changes only the spec and the note; `912a7e02` is an ancestor of the base.
> 3. xc2 spec `a9e6b463…` validates; `g1b_tasl.py`, `sweep2/g1b`, `t1_tasl_node.sh`, `g1b_tasl_join.py`, `g5_tasl.py`, `build_launch_chain.py`, PLAN.md, authorizations byte-identical to main; pins unchanged from round 2; no `approved: true`.
> 4. The stray-file check does not misfire on `mac-g5-scope-twocards-20261125` (`7146197e`): no file named `G1B_XC3_SHORT_VERDICT_*` there, on main or at the tip; `verdict-status` on real origin/main gives PENDING ×4. Nits (no action): xc3's rule is stricter than G.5's (fails closed); an unreadable PLAN on main is treated as no row, but `launch_xc` still fails closed via `verify_launch_tasl`.
> 5. `validate`, `check-xc-note --draft` ok; tests one file at a time: crosscheck 79, xc3 5, g1b 45, chain 16 passed; full-suite lists byte-identical (61 lines).

---

Code-Commit: 7594a6fb (code, tests, template; launch commit 6f4e2ba1)
Verdict: ACCEPTED

Accepted 25 Nov 2026.
