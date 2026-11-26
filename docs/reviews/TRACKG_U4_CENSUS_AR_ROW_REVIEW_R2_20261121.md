# Independent re-review (round 2) — Track G U4 census update adding the `autoresearch_fixedtokens` TASL-2 row (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer-r2`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2 host check, the AR unit/result/smoke, the U4 census or any earlier U4
review (R1–R5 or the round-1 AR-row review). **Read-only:** the only file written is this review (untracked, no
commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or live-host contact, edit of any other file,
deletion/move, HTCondor or deepthought action. Every fact below is either recomputed from the delivered bytes or
read from local git/records.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`76bf88db22cc7ad40c9ec9588a7eaad1e9d228539321b6a04018d0dccca48751`**, **115 lines / 11,734 bytes**, mtime
**2026-11-21T03:59:34Z**, **tracked and modified** in the worktree at HEAD **`ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`**
(`origin/ops-tasl-20261116` = same; `origin/main` = `4aac5209`). The HEAD blob is `6d1ac47f…` = SHA-256
`146b111410122108c7efa25246b61db62060adcaa3ea14fb2111ec2e13d692d7`, 109 lines, i.e. the R5-accepted/C1-repaired
census committed at `76f1d7ba`; the working-tree delta is **+29/−23 lines** and touches only the eighth row, the
run-level AR row/"All eight rows" text, the per-suite autoresearch bullet, the new `AR row measurement notes`
paragraph, the `Blocked / not passed` bullet and the readiness paragraph. The earlier rows, funnel appendix,
kitchen/environment, licence paragraph and acceptance citations are byte-identical to HEAD.

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_20261121.md` SHA-256
**`4733a891287b6137f94c3765b1e23612ebfd92d4b49b02895796b36cf2ed95f9`** (302 lines) — **NOT ACCEPTED, 0 BLOCKING,
2 MAJOR (report-only: stale appendix; half-integration), 11 MINOR, 1 dependency finding, conditions C1–C8**. Its
object (`8c0c0173…`, 101 lines / 10,251 B) was overwritten in place at 03:59:34Z by the current file and is **not
preserved** in git or the workspace (it is cited only by that review), so the round-1→round-2 delta can be audited
against the prior review's verbatim quotes plus the HEAD→current diff, not byte-for-byte. Traceability note t1.

**Inputs / authority read (all local, read-only; no live host was contacted).** The AR U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` SHA-256 **`8430854c…`**, 67 lines / 5,181 B, mtime 03:59:34Z (the reviewed
object `ca3bcadd…`, 57 lines / 3,893 B, is not preserved); its review
`U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` **`9de24ec5…`** (212 lines; **ACCEPTED — 0 BLOCKING, 1 MAJOR
report-only, 12 MINOR, conditional on C1–C5**); the executed-unit copy beside the result
`U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` **`b83d9159…`**, 74 lines / 6,374 B, byte-identical to the committed
unit `docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md` (committed `d65079af`), whose review
`TRACKG_U2_ISO_AUTORESEARCH_UNIT_REVIEW_20261121.md` **`ef42276d…`** reviewed the 56-line object `3bb015a1…`; the
smoke result `TASL2_AR_COND7A_RESULT_20261121.md` **`8814eecc…`**, 288 lines / 22,667 B, and captures
`TASL2_AR_COND7A_RESULT_20261121_captures/` (`SHA256SUMS` **`32f5009a…`**, **7,055 entries**, 7,056 files + 17
symlinks, `shasum -a 256 -c` **rc 0 / 7,055 OK**); the TASL-2 host-check report (current **`83636c03…`**, mtime
**04:00:26Z**, i.e. amended *after* the census mtime; the reviewed object in the AR references is
`0a1fa3a4…`) and its review **`bfe9b231…`** (**ACCEPTED for the AR option-A gate; 0 BLOCKING, 1 MAJOR report-only,
6 MINOR, C1–C4**; §3 item 7 CUDA IPC UNTESTED, §5 item 5/5.5 open); the 17 Nov Ada un-isolated baseline
`TRACKG_U2_AR_RESULT_20261117.md` **`a6ddfbd0…`** (wall 564 s / 9:23.68, B1 67.901 s, `val_bpb` 1.291068, L40S,
5,211.3 MB); the 20 Nov STOP `U2_ISO_AR_COND7A_RESULT_20261120.md` **`bcb74efc…`**; the 21 Nov retry STOP
`R1_TRACKG_AR_COND7A_RETRY_RESULT_20261121.md` **`34bd3532…`** (2 attempts, 0 run records); the committed addendum
`TRACKG_U4_CENSUS_ADDENDUM_20261121.md` **`fa7bb75d…`** (at HEAD); R5 review `TRACKG_U4_CENSUS_REVIEW_R5_20261120.md`
**`9c604f1b…`**; `docs/r1/PLAN.md` at HEAD **`ebe03cd5`** (1,337 lines; `R1-TRACKG-G0-GO` :1258 — also at `de3de54f`
which has 1,317 lines and no :1330; `R1-TRACKG-AR-COND7` :1317; `R1-T1-HOST-H200` :1329; `R1-TRACKG-G3-EARLY` :1330);
`U1_LICENCE_AVAILABILITY_20261117.md`; the AR captures parsed directly (9 `run_record.json` = 8 executed + refused
`s001`; `time_v.txt`; `disk_before/after.txt`; `pins*.txt`; `data_manifest.txt`; `sampler/sampler_max.json`;
`slowdown.json`; `memory_cgroup.txt`; `gate/gate_not_applicable.txt`; `gpu/*`; `verify_full.json`; `facts.json`;
`RESULT_STATUS*`; `references/`). The census was cell-counted and `pandoc -f gfm` render-checked. Nothing was re-run
and no live host was contacted.

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 12 MINOR, 1 traceability note, conditions C1–C8 below (documentation/
record only; no re-run, no measured-value change).** **Both prior MAJORs are closed:** the per-suite appendix no
longer contradicts the table, and the row is integrated into the run-level facts, the gate envelope, the counts and
readiness. The 15 cells of the AR row and every AR measurement note reproduce from the delivered records; there is
no fabricated or overclaimed measured value. The remaining defects are **record/citation accuracy**: the
executed-unit provenance sentence is inaccurate (it says the executed amended unit is "in the captures"; the
bundle contains no unit copy and the census omits sha `b83d9159…`), the U2 result review is still recorded as
unconditionally "C1–C5 applied", the acceptance-citations section still carries no AR review/report shas, and
several round-1 MINOR/condition items remain open. **C1 and C2 must be applied before the census is committed**;
C3–C8 are the remaining documentation corrections.

---

## 1. Closure of the two prior MAJORs

### 1.1 MAJOR-1 (per-suite appendix still said autoresearch was "not in this census"/STOPPED) — **CLOSED**

The appendix bullet (lines 60–65) now reads:

> "**autoresearch (1 node):** **passed** on TASL-2 under author-signed `R1-TRACKG-AR-U2-TASL2` with option A: one
> clean isolated smoke, B1 218.951 s/val_bpb 1.293937, B2 218.443 s exact, isolation effective/no waivers/no CUDA
> IPC, slowdown 3.225× vs the 17 Nov Ada un-isolated U2 67.901 s (cross-host), transfer 0.2345 s/request; result
> review ACCEPTED with C1–C5 (text conditions applied). The 20 Nov Ada co-tenant OOM and the 21 Nov retry STOP
> remain preserved as historical external-contention evidence, superseded by the TASL-2 clean smoke. T1 labels
> remain on H200."

"not in this census", "was attempted and STOPPED", "slowdown not measured" and "joins after a fresh clean isolated
smoke + U2 review" are gone; the appendix, the table (line 21) and the Blocked bullet (lines 90–96) are now
consistent that autoresearch passed on TASL-2, that the 20 Nov OOM and 21 Nov retry STOP are historical, and that
T1 labels remain H200 (`PLAN:1329`). The `grep` for "not in this census"/"not run"/"seven" returns nothing. ✅

### 1.2 MAJOR-2 (row not integrated into run-level facts, gate envelope or counts) — **CLOSED in substance**

- **Run-level facts:** the eight-row table (lines 25–34) gains the AR row with whole-smoke max RSS **3,204,520 kB**
  (`time_v.txt`), deployed run-record pin **`ca049086…`** (21 entries, path-dependent; Ada value `069e987a…`), gate
  capture `gate/gate_not_applicable.txt` (`paper_a_gate=NOT_APPLICABLE_ON_TASL2`, substitute controls), disk
  **388,531,040,256 → 388,344,332,288 B** (`disk_before/after.txt`). All verified.
- **Gate envelope:** line 42 now states "Paper-A three-check gate clear (**AR row on TASL-2 has no Paper A;
  exclusivity controls and no other compute app recorded instead**)", and the Blocked bullet and run-level cell
  repeat the substitution. This closes the prior MAJOR-2 requirement to disclose that the row was measured without
  the Paper-A gate.
- **Counts:** "All seven rows" is now "All eight rows" (line 40); the readiness paragraph says all eight are set.
- **Residuals (MINOR, not MAJOR):** the gate capture cell has a malformed path (m4); the sentence "Each row's gate
  JSON is `clear_finished`…" (lines 36–38) is false for the eighth row (m4); the 20,000 MiB qualifier floor / env /
  data-root / single-smoke-as-pre-U2-gate adaptations are not disclosed (m5); the citations section is untouched
  (m3). None re-opens MAJOR-2: the row is now integrated and the gate/floor substitution is disclosed (gate) or
  minor-omitted (floor).

## 2. Mechanical checks (all pass; no formatting regression)

- Main table: header, delimiter and **all 8 data rows = 15 cells each**. Run-level table: header, delimiter and
  **all 8 data rows = 5 cells each**. `pandoc -f gfm -t html` emits **two tables**, **18 `<tr>`** and **20 `<th>`**
  (15 + 5). No broken pipes.
- The working-tree diff is **+29/−23**; the seven earlier rows, run-level rows, funnel appendix, kitchen/environment,
  licence paragraph and citations are byte-identical to the HEAD blob (`git diff`).
- The prior review's findings m3–m11 are resolved to the extent recorded here; the citation and naming items remain
  (m3/m8/m9).

## 3. The AR row — all 15 cells verified from the records (no value taken from the census)

| # | cell | census value | verified against | result |
|---|---|---|---|---|
| 1 | node | `autoresearch_fixedtokens` | run records / result title | ✅ |
| 2 | suite | `autoresearch` | U1 §2; smoke report | ✅ |
| 3 | kit tip | `7330338…` | smoke §2.2 `73303380197477…`; `kit.txt` | ✅ (7-char abbreviation, m8) |
| 4 | B1 elapsed | `218.951 s` | `runs_smoke/s000_baseline/run_record.json` | ✅ |
| 5 | B1 metric | `1.293937 (val_bpb)` | same record `outcome.value`; `run.log` AR_INFO | ✅ |
| 6 | B2 elapsed | `218.443 s` | `runs_edits/B2/run_record.json` | ✅ |
| 7 | B2 metric | `1.293937 (val_bpb)` | identical to B1 (exact repeat) | ✅ |
| 8 | sealed test | `n/a` | `sealed: null` in every record | ✅ |
| 9 | timeout = 3×B1 | `656.853 s` | 3 × 218.951 = 656.853 (same rule as the seven rows) | ✅ |
| 10 | whole-smoke upper bound | `12,436 MiB` | `sampler/sampler_max.json` `max_per_sample_sum_mib: 12436` (labelled upper bound) | ✅ |
| 11 | GPU/cpus | `GPU-4d623e76…` (TASL-2 4090), cpus 0-7 | records `limits.gpu_uuids` / `cpu_list [0..7]`; host §2.1 | ✅ |
| 12 | committed-file pin | `147f0d35…` | `prep/pins_committed.txt` (20 entries) | ✅ |
| 13 | data manifest sha256 | `ab7186d2…` | `data_manifest.txt`; 13 files / 1,009,004,449 B / 963 M | ✅ |
| 14 | record | `U2_ISO_AUTORESEARCH_RESULT_20261121.md` | file exists; captures dir exists | ✅ exists; semantics/format m8 |
| 15 | licence/availability | `autoresearch MIT/climbmix MIT-claimed; option A CPU transport` | U1 §2/§7: code MIT declared (README; no LICENSE file), climbmix MIT declared on the HF card (uploader assertion) | ✅-ish, m9 |

No 17 Nov un-isolated value (67.901 s / 5,211.3 MB / 1.291068) is used as a TASL-2 row value. The row is a real
isolated option-A TASL-2 measurement: every executed record `isolation.effective:true`, `waivers {}`,
`exceptions []`, private `/dev/shm`, no CUDA IPC; `verify_full.json` `ok:true`, `issues:[]`, `ipc_hits:[]`, 8 executed
+ refused `s001`; `CHECKLIST_E_PASSED`; no synthetic marker; slowdown measured. **No fabricated value was found in
the AR row.**

## 4. Run-level facts and the AR measurement notes

Every new AR note value reproduces independently:

- whole-smoke wall **1,791.0 s** = lease window 01:58:19→02:28:10Z; `/usr/bin/time -v` elapsed **1,789.26 s**
  (`29:49.26`); **3.176×** the 17 Nov **564 s** smoke = 1,791/564 (the `564 s` reference is the 17 Nov result's
  `wall 564 s (9:23.68)`; the report's own basis).
- worker peak VRAM **1,980.1 MB** (baseline/B2/s002/s003/E1/E3), max run **3,720.4 MB** (E2) — `slowdown.json`
  `per_run_peak_vram_mb_worker`.
- parent peak **6,560.3 MB** — `runs_smoke/s000_baseline/run.log` `AR_INFO parent_peak_vram_mb=6560.3`.
- cgroup peak **5.17 GiB** = `memory.peak 5,550,911,488 B` (5.1698 GiB); `events max 0 / oom 0 / oom_kill 0`;
  `memory.swap.max 0`; sampler max current 5,550,727,168 B — `memory_cgroup.txt`, `slowdown.json`.
- sampler upper bound **12,436 MiB** (`max_single_row_mib 7,848`, 3,506 rows / 1,777 samples / 1,786.7 s / 16 pids) —
  correctly labelled upper bound, not a per-run peak.
- CPU memfd transport, no CUDA IPC — node AST scan `CUDA_IPC_API_HITS= NONE` (`kit.txt`); `ipc_hits:[]`.
- committed pin **`147f0d35…`** (20 entries) / deployed TASL-2 **`ca049086…`** (21 entries, data link
  `/home/dowling/r1_trackp/data/autoresearch_fixedtokens`); Ada value `069e987a…` correctly not expected here.
- one clean smoke is the U2 measurement, no second U2 run — U2 review §1 confirms **one** launch, one evidence root,
  exactly 9 records, no second AR run root; retry session had **0** run records.
- "no Paper A gate on TASL-2 with exclusivity substitute" — `gate/gate_not_applicable.txt`
  (`paper_a_gate=NOT_APPLICABLE_ON_TASL2`; 0 compute apps at launch, exclusive `flock`, 1 s sampler, co-tenant abort
  monitor; 879 ticks / 0 foreign apps; GPU before/mid/after idle).
- "author row not yet on main" — `R1-TRACKG-AR-U2-TASL2` is absent from committed `docs/r1/PLAN.md` at HEAD and
  `origin/main` (grep: reports only); the result/check reports describe it as author-signed and "reaches main after
  the sweep-2 launch". The census records this correctly ("not yet in committed PLAN at review time").
- "executed unit copy sha b83d9159" — **NOT met** (m1): the census says "executed amended unit in the captures" but
  the captures bundle contains no unit copy (`references/` has 6 files: retry result, host-check report/review,
  code unit, 17 Nov result, 20 Nov result; `grep` of the 7,055-entry `SHA256SUMS` finds no `U2_ISO_AUTORESEARCH_UNIT`
  entry and no `b83d9159`/`3bb015a1`), and sha `b83d9159…` is not cited in the census. The copy exists **beside the
  result**, `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` (74 lines, byte-identical to the committed Ada-targeted
  unit, still naming Host Ada / `envs/torch312` / the Ada data root / Paper A gate / 40 GiB); the TASL-2 adaptations
  are listed in the U2 result text, not in that file. The prior review said "do not assert it"; the revision
  re-asserts a captures copy.
- reviewed unit sha `3bb015a1…` not preserved — **correct**, recorded residual (only the unit review and the result
  cite it).

**Observation (not a census defect).** The captures disagree with themselves on the disk-after value:
`disk_after.txt` says **388,344,332,288 B** (used by the census), while `RESULT_STATUS.txt`/`facts.json` say
**388,344,274,944 B**; the census uses the `disk_*` capture pair consistently and matches the expected before/after.

## 5. Appendix / Blocked / Readiness / Citations

- **Appendix** — closed (see §1.1). ✅
- **Blocked / not passed** — correctly says all eight passed, no node blocked; identifies TASL-2, the author-signed
  row, B1 218.951 vs Ada 67.901 = 3.225× cross-host, transfer 0.2345 s/request, B2 exact, isolation flags, no CUDA
  IPC, slowdown measured, and preserves the 20 Nov/21 Nov external-contention history. The bullet still says "one
  host difference TASL-2/4090 vs the earlier Ada attempt" (census text line 92; should name the 17 Nov Ada
  **un-isolated** U2 and list the env/data-root/floor substitutions) and "TASL-2 host checks PASS/accepted" without
  the item-7-untested caveat (m5/m10).
- **Readiness** — `R1-TRACKG-G3-EARLY` says autoresearch joins as soon as its U2 passes (`PLAN:1330`); the U2
  passed, so "autoresearch joins the table" is right; the author row is flagged not in committed PLAN; T1 labels on
  H200 per `R1-T1-HOST-H200` (`PLAN:1329`); "All eight rows are complete"; the census does not block G.1b/G.4 and is
  not evidence. ✅ (the completion claim should carry the U2 review's conditional C1–C5, m2/m11.)
- **Authority and acceptance citations** (lines 109–115) — **still the pre-AR state**: no AR result review, no U2
  result/smoke/captures sha, no host-check report/review, no `R1-TRACKG-AR-COND7` (:1317), no `R1-T1-HOST-H200`
  (:1329), no author-row provenance; and `six isolated U2 result reviews` is wrong — there are **three** result
  reviews covering the six earlier nodes (`U2_ISO_RESULTS…`, `U2_ISO_BREAKOUT_RESULT…`, `U2_ISO_HOUSEPRICE_RESULT…`)
  plus the AR result review. This is the R5-C6 and round-1-C5 residual (m3).

## 6. Dependency — status of the AR U2 result review's conditions C1–C5 (the census says "C1–C5 applied")

| condition | status in the records | evidence |
|---|---|---|
| **C1** executed-unit record | **partially applied** | The U2 result (8430854c, lines 10–15) cites reviewed unit `3bb015a1…` and amended unit `b83d9159…` and lists the TASL-2 adaptations; a copy of `b83d9159…` exists beside the result (but it is the Ada-targeted unit, and it is not in the captures). The census's "in the captures" phrasing is inaccurate (m1). |
| **C2** land the census/U4 update | **applied** | Row landed; wall 1,791.0 s, 3.176×, worker peak 1,980.1 MB, cgroup 5.17 GiB are recorded in the census. |
| **C3** host-check C1–C4 + author-row record | **not applied to the record trail** | Host-check report was amended at **04:00:26Z** (sha `83636c03…`, after the census mtime) to add the item-7-untested wording, but its review conditions C2–C4 text/author-row items and the author-signed row/delegation text are still not in the committed PLAN or a preserved record-trail file (host-check review m4/C3; U2 review C3). |
| **C4** report accuracy (m4–m12) | **partially applied** | U2 result now discloses the 20,000 MiB floor (line 12) and the bundle-byte basis (line 59), and adds the no-evidence statement (lines 65–66); **not** applied: parent peak `6,560.3 MB` absent from the U2 result; "B1/B2 median 218.7935 s" mislabel (line 43); "1,791.0 s (29:49)" shorthand (line 45); the smoke report still says "16.6 KB (`s001`)" (line 174; the U2 result correctly gives 166,300 B); author-row provenance. The census itself carries the parent peak, which satisfies the round-1 C3 ask for the census. |
| **C5** verification integrity | **satisfied** | One smoke, no re-run; smoke report `8814eecc…` and captures `32f5009a…` unchanged; verifier rc 0 / `issues:[]`. |

So "C1–C5 applied" (appendix line 63) and "review ACCEPTED, C1–C5 applied" (notes lines 74–75) **overstate**: the
review was ACCEPTED **conditional on C1–C5**, and C3/C4 residuals remain. This is m2; it matters because the census
is the admission record for the row and the row is a U4 raw-cost row, not T1 evidence.

## 7. Findings

**BLOCKING: none. MAJOR: none (both prior MAJORs closed).**

### MINOR

- **m1 — executed-unit provenance is misrecorded (record accuracy; C1 mandatory before commit).** Lines 74–75 say
  "executed amended unit in the captures"; the 7,056-file/7,055-entry captures bundle contains no unit copy
  (`references/` = 6 files, none is a unit), and sha `b83d9159…` is not cited in the census. The sibling
  `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` (`b83d9159…`, 74 lines) is byte-identical to the committed
  Ada-targeted unit (Host Ada, `envs/torch312`, Ada data root, Paper A gate, ≥40 GiB floor) — i.e. it is the
  post-review amended unit, **not** a TASL-2-adapted executed unit; the TASL-2 adaptations are recorded only in the
  U2 result text. The prior round said "do not assert it"; correct to "executed-unit record listed in the U2 result
  text; amended unit copy `b83d9159…` beside the result (not in the captures); reviewed `3bb015a1…` not preserved"
  or preserve a real TASL-2 executed-unit record. No re-run.
- **m2 — "review ACCEPTED, C1–C5 applied" overstates the dependency** (appendix line 63, notes lines 74–75). The U2
  result review (`9de24ec5…`) is **ACCEPTED conditional on C1–C5**; C3 (author-row record) and C4 residuals (parent
  peak in the U2 result, median label, `1,791.0 s/29:49` shorthand) are not applied. Cite "ACCEPTED conditional on
  C1–C5", the review sha `9de24ec5…`, the current U2 result sha `8430854c…` and the reviewed-object `ca3bcadd…`
  delta, and list the open residuals. (Round-1 C3/m11.)
- **m3 — acceptance/authority citations still pre-AR (round-1 C5/C8; R5 C6).** No AR result review, U2 result, smoke
  report/captures, host-check report/review, `R1-TRACKG-AR-COND7` (:1317), `R1-T1-HOST-H200` line attribution (:1329;
  the readiness paragraph names the row but the citations section does not) or author-row provenance; "six isolated
  U2 result reviews" is wrong (three result reviews for the six earlier nodes, plus the AR result review); the
  fix-review filename is still duplicated (R5 C4). Give filenames + shas; if the host-check report is cited, cite the
  amended `83636c03…` (and note it is the C1-amended successor of reviewed `0a1fa3a4…`).
- **m4 — run-level gate cell path is malformed; the "each row's gate JSON" sentence is false for AR.**
  `TASL2_AR_COND7A_RESULT_20261121.md/gate/gate_not_applicable.txt` uses the report `.md` as a directory; the
  capture is `TASL2_AR_COND7A_RESULT_20261121_captures/gate/gate_not_applicable.txt`. Lines 36–38 ("Each row's gate
  JSON is `clear_finished`, key false, `paper_a_processes []`…") do not describe the AR row, which has no gate JSON;
  qualify it.
- **m5 — TASL-2 adaptations incomplete (round-1 C2/m3).** The 20,000 MiB qualifier floor replacing the 40 GiB floor,
  env `ar-cond7a` (Py3.12.15), data root `/home/dowling/r1_trackp/data`, and the single clean smoke serving as both
  the pre-U2 gate and the U2 run are not disclosed; the Blocked bullet still says "one host difference … vs the
  earlier Ada attempt" (name the 17 Nov Ada un-isolated U2 and the adaptations) and "3.225× cross-host option-A
  slowdown" (label the composite: option A + host change; bpb/VRAM not normalised); `0.2345 s` should be labelled a
  wall-clock surrogate.
- **m6 — "no retry" contradicts the disclosed retry (round-1 m8).** Header lines 7–8 ("one accepted unit and one
  smoke per node (no retry)") and line 40 ("one executed smoke, no retry") coexist with the disclosed 20 Nov failed
  smoke and "21 Nov retry STOP" (lines 63–64, 94). Qualify: "one executed TASL-2 smoke; no retry within the TASL-2
  session; the earlier Ada attempt and the 21 Nov retry session (0 run records) are preserved as external-contention
  STOPs".
- **m7 — title/date and the superseded addendum (round-1 m9).** The title still says "20 November 2026" although the
  census now carries a 21 Nov row; record the update date and revision sha. The committed
  `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` (`fa7bb75d…`, at HEAD `ebe03cd5`) still says "No U4 measured row or accepted
  number changes: autoresearch remains **blocked** and is not a U4 row" and is neither marked superseded nor
  referenced; the record trail is self-contradictory until this is fixed.
- **m8 — record cell and table formatting (round-1 m6).** Every other row's `record` cell is a record directory; the
  AR row cites the U2 *result report* only and no captures/record sha. Cite
  `TASL2_AR_COND7A_RESULT_20261121_captures/` (`SHA256SUMS` `32f5009a…`, 7,055 entries, rc 0) beside the result.
  Formatting: 7-char kit-tip `7330338…` vs 8 elsewhere; GPU "(TASL-2 4090)" vs "(card n)" elsewhere.
- **m9 — licence/availability cell (round-1 m7).** "option A CPU transport" is methodology, not licence, and
  availability is missing. Per U1 §7: code MIT declared in README (no LICENSE file); climbmix dataset MIT declared
  on the HF card (uploader assertion); public/HTTP 200; data present (963 M, manifest `ab7186d2…`).
- **m10 — host-check caveat missing (round-1 m2).** "TASL-2 host checks PASS/accepted" should say: for the **AR
  option-A gate only**; §3 item 7 CUDA IPC remains **UNTESTED**; §5 item 5/5.5 open; no `cuda_share`/`cuda_open`
  node may start on its strength. The amended host report (`83636c03…`, 04:00:26Z) now carries this wording; cite it.
- **m11 — authorizations/completion qualifiers (round-1 m1/m5/m11).** "author-signed `R1-TRACKG-AR-U2-TASL2`" and
  "reaches main after the sweep-2 launch" are report claims: the row/delegation text is not in committed PLAN nor in
  a preserved record-trail file (host-check review m4/C3). Record where the signed row/delegation is preserved, and
  qualify "All eight rows are complete" with the U2 review's conditional C1–C5 and the fact that the AR row is an
  ENGINEERING_ONLY U2 raw-cost row (not T1).
- **m12 — R5 carried conditions not recorded as open (round-1 m10/C7).** R5's documentation conditions C2–C10 are
  still open (C4 duplicate fix-review name at lines 81–82; C5 licence column vs U1 §7; C6 citations; C7 imdb
  verbatim sentence; C8 CPU/RAM wording; C9 preserve the reviewed revision; C10 committed-AR-evidence SHA256SUMS).
  Record them as open (or close them) so the final census is not committed with unrecorded conditions.
- **t1 — traceability (not a finding against a value).** The round-1-object census (`8c0c0173…`) was overwritten in
  place at 03:59:34Z and is not preserved; use the HEAD→current diff plus the prior review's quotes for audit. Bind
  acceptance to `76bf88db…` and preserve the accepted revision (and any successor) with its sha.

## 8. Conditions (documentation/record only — no new run, no measurement/record edit)

- **C1 (mandatory before commit; m1).** Correct the executed-unit record: state that the executed amended unit copy
  is the sibling `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` (`b83d9159…`, 74 lines; byte-identical to the
  committed Ada-targeted unit, so the TASL-2 adaptations exist only as the U2 result's declared deviations), that it
  is **not** in the captures, and that reviewed unit `3bb015a1…` is not preserved; or preserve a real TASL-2
  executed-unit record. Do not assert a captures copy that does not exist. No re-run.
- **C2 (mandatory; m2/m11).** Qualify the U2 acceptance as **ACCEPTED conditional on C1–C5**, cite review
  `9de24ec5…`, record the current U2 result sha `8430854c…` (reviewed object `ca3bcadd…` not preserved) and the open
  C3/C4 residuals; record the author-signed row/delegation provenance or where it is preserved.
- **C3 (m3).** Complete the acceptance/authority citations with report/review shas: U2 result `8430854c…`, result
  review `9de24ec5…`, smoke report `8814eecc…`, captures `SHA256SUMS` `32f5009a…` (7,055/7,055 rc 0), host-check
  report `83636c03…` (amended; reviewed `0a1fa3a4…`) + review `bfe9b231…`, `R1-TRACKG-AR-COND7` (:1317),
  `R1-T1-HOST-H200` (:1329), author-row provenance; fix "six isolated U2 result reviews" → three result reviews
  covering six nodes (+ the AR result review) and remove the duplicated fix-review filename.
- **C4 (m4/m5).** Fix the gate-capture path to
  `TASL2_AR_COND7A_RESULT_20261121_captures/gate/gate_not_applicable.txt`; qualify the "each row's gate JSON"
  sentence; disclose the 20,000 MiB floor / `ar-cond7a` env / data root / single-smoke-as-pre-U2-gate; name the
  17 Nov Ada un-isolated baseline in the Blocked bullet; label 3.225× as a cross-host composite (option A + host
  change, bpb/VRAM not normalised) and 0.2345 s as a wall-clock surrogate.
- **C5 (m6/m7).** Qualify the "no retry" statements with the 20 Nov failed smoke and 21 Nov retry session (0 run
  records); add the 21 Nov revision date/sha to the title or a revision line; mark
  `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` superseded or reference it (or amend it) so the committed trail is not
  self-contradictory.
- **C6 (m8/m9/m10).** Fix the record cell to the captures dir + `SHA256SUMS` sha; fix the licence/availability cell
  per U1 §7; add the host-check caveat (AR option-A gate only; item 7 CUDA IPC UNTESTED; §5 item 5/5.5 open).
- **C7 (m12/t1).** Record that R5's carried conditions remain open (or close them); bind acceptance to census
  SHA-256 `76bf88db…` and preserve the accepted revision. If C1–C6 change the text, record the successor sha; only
  these listed text corrections are permitted without a fresh substantive review.
- **C8 (evidence/traceability).** Commit the census together with the cited AR evidence
  (`U2_ISO_AUTORESEARCH_RESULT_20261121.md` `8430854c…`, unit copy `b83d9159…`, smoke `8814eecc…`, captures
  `32f5009a…`, U2 review `9de24ec5…`, host check + review, retry/20 Nov references) and record the shas; the AR
  row's 15 values are verified and must not change. No re-run, no smoke, no second U2, no measurement/record edit is
  permitted or required by this review.

## 9. Acceptance binding and read-only attestation

Acceptance binds to the reviewed content
`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`76bf88db22cc7ad40c9ec9588a7eaad1e9d228539321b6a04018d0dccca48751`**, 115 lines / 11,734 bytes, mtime
2026-11-21T03:59:34Z, tracked-modified at HEAD `ebe03cd5` (HEAD blob `6d1ac47f…` = `146b1114…` preserved). The
verdict is **ACCEPTED with conditions C1–C8** (C1/C2 mandatory before commit); the two prior MAJORs are closed and
the measured AR row is correct. **Written:** only this review file. **Read-only:** all cited files and captures;
`shasum -a 256`; `shasum -a 256 -c SHA256SUMS` (captures 7,055/7,055 OK, rc 0); JSON parses of the AR records,
`verify_full.json`, `sampler_max.json`, `slowdown.json`, `memory_cgroup.txt`, `pins*`, `data_manifest.txt`,
`time_v.txt`, `disk_*`, `gate/gate_not_applicable.txt`; `git rev-parse/log/diff/status/show/cat-file`; `wc`, `stat`,
`grep`, `pandoc -f gfm` render check. **Not done:** no run, smoke, U2/GPU/T1/census job, probe, SSH/live-host
inspection, file edit outside this review, commit, push, deletion/move, HTCondor/deepthought action, or
secret/credential read. No other review's object was modified.
