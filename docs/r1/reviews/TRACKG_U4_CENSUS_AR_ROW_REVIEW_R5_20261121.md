# Independent final review (round 5) — Track G U4 census AR-row update and binding sidecar after R4 NOT ACCEPTED (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer-r5`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2/TASL-7 host checks, the AR unit/result/smoke, the U4 census, the
binding sidecar, or the earlier U4 reviews (seven-node R1–R5; AR-row R1–R4). **Read-only:** the only file written
is this review (untracked; no commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or live-host contact,
edit of any other file, deletion/move, HTCondor or deepthought action. Every fact below is recomputed from the
delivered local bytes or read from local git/records. (`shasum -a 256 -c` over the delivered AR capture bundle is
a read-only integrity check, not an experiment run.)

**Objects under review (the pair).**

| object | SHA-256 | size | mtime | git state |
|---|---|---|---|---|
| census `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md` | **`ef001f890b29c2b8c75e072556f1172562a874726a4d3378604e1567e3e3308e`** | **139 lines / 14,565 bytes** | **2026-11-21T04:25:41Z** | **tracked-modified**; worktree HEAD **`ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`** = `origin/ops-tasl-20261116`; `origin/main` `4aac5209`; HEAD blob `6d1ac47f…` = `146b1114…` (109 lines / 10,925 B); diff vs HEAD **+60/−30 lines** |
| binding sidecar `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md` | **`f5c781d4ccc69e3cf520ee6e1e2461cb4d6b36e5208c45ff58e74b7c90963a48`** | **10 lines / 2,207 bytes** | **2026-11-21T04:25:47Z** | **untracked** (`??`); binds the census sha `ef001f89…` exactly |

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_R4_20261121.md`, SHA-256
**`d4c3f9f06a97b6fe94ad2171365183bd53d11de7ce740206c42b4d212f8b4523`** (255 lines / 25,428 B, mtime
04:24:39Z) — **NOT ACCEPTED, 0 BLOCKING, 3 MAJOR (record/traceability: C1, C2, C5), 4 MINOR, 1 traceability note**.
Its object (SHA-256 `2dbf2c16…`, 136 lines / 13,984 B, mtime 04:17:39Z) is **not preserved**: no working-tree copy
and no git object. The R3 object (`79ad29ca…`, 123 lines / 12,634 B) and the R5 seven-node object (`4e050ad2…`,
109 lines / 11,207 B) are likewise not preserved; only the HEAD blob `146b1114…` is in git.

**Inputs / authority read (all local, read-only; no live host was contacted).** U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` **`ee21f6d9e8bb3fd807809c54cdfb039ff1643c07f7950b88e5e5a770bb480be4`**
(73 lines / 5,484 B, mtime 04:17:39Z, untracked); its review `U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md`
**`9de24ec5…`** (ACCEPTED, conditional C1–C5; reviewed object `ca3bcadd…` = 57 lines / 3,893 B, not preserved);
executed-unit sibling `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` **`b83d9159…`** (74 lines / 6,374 B, verified
byte-identical to the unit committed at `d65079af`: `docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md`;
not in the captures); smoke `TASL2_AR_COND7A_RESULT_20261121.md` **`8814eecc…`** (288 lines / 22,667 B, PASS); its
captures `TASL2_AR_COND7A_RESULT_20261121_captures/` — `SHA256SUMS` **`32f5009a…`**, **7,055 entries**,
**7,056 regular files**, 17 symlinks, 2,128 dirs, `shasum -a 256 -c` → **rc 0, 7,055/7,055 OK**; TASL-2 host-check
report **`83636c03…`** (reviewed predecessor `0a1fa3a4…`, 369 lines) / review **`bfe9b231…`**; TASL-7 host-check
report **`2b703226…`** / review **`18e261cd…`**; AR-row R2 review **`5fe423ac…`** (object `76bf88db…`, 115 lines /
11,734 B) and R3 review **`4c5f1848…`** (object `79ad29ca…`); seven-node R5 review **`9c604f1b…`** (ACCEPTED,
object `4e050ad2…`); superseded addendum **`fa7bb75d…`**; `docs/r1/PLAN.md` at HEAD and `origin/main`
(`4aac5209`; `df58bcd5` is an ancestor) — `R1-TRACKG-AR-COND7` :1317 (also at `df58bcd5`:1317), `R1-T1-HOST-H200`
:1329, `R1-TRACKG-G3-EARLY` :1330, `R1-TRACKG-G0-GO` :1258, `R1-TRACKG-LICENCES` :1269,
`R1-TRACKG-PORT-DECISIONS` :1289, `R1-HARNESS-ISOLATION` :1290 all verified present (the author-signed
`R1-TRACKG-AR-U2-TASL2` row is absent from both committed PLANs, as the census/sidecar say); the seven earlier
record directories and their gate JSONs; the AR captures parsed directly (9 `run_record.json` = 8 executed +
refused `s001`; every executed record `isolation.effective:true`, `waivers {}`, `exceptions []`;
`gate/gate_not_applicable.txt`; `run.log` `AR_INFO parent_peak_vram_mb=6560.3`; disk before/after captures). The
census was cell-counted (8 data rows × 15 cells main table, 8 × 5 run-level table) and rendered with
`pandoc -f gfm` (rc 0).

**Verdict: NOT ACCEPTED — 0 BLOCKING, 2 MAJOR (record-only traceability), 9 MINOR, 1 traceability note.** The
measured content is unchanged and correct — all eight rows/values verified, seven earlier rows byte-identical to
the HEAD blob, captures **7,055/7,055 OK**, no fabricated or overclaimed value, and U4 still does not block
G.1b/G.4 — and most of the R4 MAJOR substance is now fixed (current U2 sha cited; authority rows and review
count fixed; sidecar binds the exact current census sha; duplicate fix-review name removed; labels added). But **R4's C1
is not closed and C5 is only partly closed**: the two traceability deltas recorded in the census and in the
binding sidecar are **wrong** (the `+6 lines/+280 B` figure is the `c03f0cbd→ee21f6d9` step, not
`ca3bcadd→ee21f6d9`, which is `+16/+1,591`; the `+13 lines/+1,350 B` figure is the R3→R4-object step, not
R3→current, which is `+16/+1,931`), the intermediate U2 chain/steps and several R4-C1 items are still missing, the
U2 result's own revision note is still false and contradicts the census/sidecar, and R5's carried conditions are
still not recorded. Because the binding sidecar is the acceptance record and its chain figures are wrong, this
pair cannot yet be taken as the final U4 record/binding.

---

## 1. Confirmations that do hold (measured content unchanged; citations/labels fixed; binding sha exact)

- **Seven earlier rows unchanged.** The main-table rows 1–7 and run-level rows 1–7 are **byte-identical** to the
  HEAD blob `146b1114…` (extracted with `git show HEAD:…` and row-diffed; only the AR row was added). Their seven
  gate JSONs re-parse `verdict:"clear_finished"`, `paper_a_live_waiting_for_card:false`,
  `paper_a_processes:[]` (all seven checked). Their measured values are therefore unchanged and remain covered by
  seven-node R5.
- **AR row values unchanged and independently re-verified from the smoke/captures.** B1 `218.951 s` /
  `1.293937 (val_bpb)`; B2 `218.443 s` / `1.293937` (exact); sealed `n/a` (smoke reports no sealed view); timeout
  `656.853 s` (= 3 × 218.951); upper bound `12,436 MiB`; `GPU-4d623e76…` (TASL-2 4090), cpus 0-7; committed pin
  `147f0d35…`; manifest `ab7186d2…`; record cell `U2_ISO_AUTORESEARCH_RESULT_20261121.md` + captures dir +
  `7,055/7,055 OK` + `SHA256SUMS 32f5009a…`. The run-level AR row matches the captures: `3,204,520 kB` max RSS;
  deployed pin `ca049086…`; `gate_not_applicable.txt`; disk
  `388,531,040,256 → 388,344,332,288 B`. The AR notes match: `1,791.0 s`, `3.176×` (1,791.0/564 = 3.176),
  `1,980.1 MB`, `3,720.4 MB`, `6,560.3 MB` (capture `run.log AR_INFO parent_peak_vram_mb=6560.3`), cgroup
  `5.17 GiB`, sampler upper bound `12,436 MiB`, CPU memfd/no CUDA IPC, pins 20/21.
- **Captures unchanged and complete.** `SHA256SUMS` **`32f5009a…`**, 7,055 entries, 7,056 regular files, 17
  symlinks, 2,128 dirs; `shasum -a 256 -c` → **rc 0, 7,055/7,055 OK** (Mac copy). Captures/`SHA256SUMS`
  mtimes predate all reviews; no capture edited. No re-run, no second U2, ENGINEERING_ONLY raw-cost row.
- **Citations now substantially correct.** Host-check report/review shas all match the files (`83636c03…` /
  `bfe9b231…`, `2b703226…` / `18e261cd…`); the amended TASL-2 report is recorded as successor of `0a1fa3a4…`;
  AR result `ee21f6d9…`, smoke `8814eecc…`, captures `32f5009a…`, U2 review `9de24ec5…` are correct; the
  result-review sentence now correctly says **two** reviews cover the six earlier torch nodes
  (`965dc993…` five-node result review + `d4cdd9bb…` Breakout review) plus the HousePrice result review plus the
  AR review; `R1-TRACKG-AR-COND7` (PLAN:1317), `R1-T1-HOST-H200` (PLAN:1329) and `R1-TRACKG-G3-EARLY`
  (PLAN:1330) are all cited and verified present.
- **C3 labels now present.** `:43` "no U2 retry", qualified by the header `:9–10` disclosure (20 Nov Ada STOP /
  21 Nov retry-session STOPs are not U2 retries); `:65` labels `3.225×` a **cross-host composite** (option A +
  host change) with "bpb/VRAM not normalised"; `:97` labels `0.2345 s/request` a **wall-clock surrogate**; the
  17 Nov Ada un-isolated U2 is named at `:65`. The AR smoke is a single `port_smoke_gpu`; 8 executed + refused
  `s001` verified in the captures.
- **Sidecar sha binding is exact.** The sidecar's `ef001f89…` rehashes the current census exactly (the earlier
  self-reference problem is correctly solved by binding from a sidecar written after the census), and it records
  the R5/AR-R2/R3 acceptance objects and that the R3 bytes are not preserved. Duplicate
  `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` is removed (one occurrence, `:86`); the gate wording
  (`:39–40`), `clear_finished`/key-false/`[]` claim, and the AR "no Paper A / gate_not_applicable + exclusivity
  controls" claim are all true.
- **U4 does not block G.1b/G.4 — confirmed.** `R1-TRACKG-G3-EARLY` (`PLAN:1330`) sets the six earlier nodes for
  G.1b/G.4 now and lets HousePrice/autoresearch join once their U2 passes; `R1-T1-HOST-H200` (`PLAN:1329`) keeps
  the T1 labels on H200. The census readiness text says the census does not block G.1b/G.4 and is not evidence;
  that is correct, and U4's acceptance is not a G.1b/G.4 gate.

## 2. C1 — U2 result sha/delta/unit nuance: **NOT MET** (current sha fixed, but delta/chain and required items are not)

R4 C1 (before-commit) required: the **current** U2 sha `ee21f6d9…` (73 lines / 5,484 B); the full chain
`ca3bcadd…` (reviewed, 57/3,893, not preserved) → `8430854c…` (R2-recorded, 67/5,181) → `c03f0cbd…`
(67/5,204, +23 B parent-peak) → `ee21f6d9…` (+6 lines / +280 B unit-provenance block); the sibling's 74-line size;
the open U2-review C3/C4 residual list; where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is
preserved; and correction of the U2 result's own revision note.

- **Current sha: fixed.** Census `:126` and sidecar `:7` both cite `ee21f6d9…`; it rehashes the current U2
  result. Good.
- **Delta: still wrong.** Census `:126–127` says "reviewed `ca3bcadd…`; **reviewed→current +6 lines/+280 B**
  unit-provenance block". `ca3bcadd` is **57 lines / 3,893 B** (U2 review `:14`); `ee21f6d9` is **73 / 5,484**, so
  reviewed→current is **+16 lines / +1,591 B**. The quoted `+6/+280` is the **`c03f0cbd` → `ee21f6d9`** step
  (67→73 lines; 5,204→5,484 B). The sidecar `:7` repeats the same misattribution. The intermediate steps
  `8430854c…` (+10 lines / +1,288 B) and `c03f0cbd…` (+23 B parent-peak) are **omitted entirely**, so the
  recorded chain cannot be reconstructed from the pair; the sidecar also does not cite the R2/R3 review
  documents (objects `76bf88db…`/`79ad29ca…` are named without their accepting-review shas).
- **"Reviewed" label now correct in the census, but the U2 result still contradicts it.** The census correctly
  calls `ca3bcadd…` reviewed (not `8430854c…`). But the U2 result's own revision note (`:71–72`) still says
  "This result was reviewed at sha `8430854c…`; … gives the current sha `c03f0cbd…`" — both statements are false
  (reviewed = `ca3bcadd…`; current = `ee21f6d9…`). R4 m4/C1 required this correction; the file's mtime
  (04:17:39Z) is unchanged and the note is still stale.
- **Unit nuance: partial.** Census `:138–139` correctly records that the sibling `b83d9159…` is byte-identical to
  the committed Ada-targeted unit and not in the 7,055-entry captures (verified), and that reviewed
  `3bb015a1…` is not preserved. Still missing: the sibling's **74 lines / 6,374 B**; the **open U2-review C3/C4
  residual list**; and **where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved** (it is
  absent from both committed PLANs and no record file is cited — the census only says it "is signed and reaches
  main after the sweep-2 launch").

## 3. C2 — Citation completeness: **MET** (with minor residue)

R4 C2 required: host-check report/review shas; AR result/smoke/captures; `R1-TRACKG-AR-COND7` (PLAN:1317) and
`R1-T1-HOST-H200` (PLAN:1329); and a fix of the result-review count/phrasing. All are present and verified
(§1). Residuals (MINOR m1): the old citations block was left behind as a dangling fragment at `:130–133`
(duplicate result-review names, HousePrice unit/result names, "isolation fix review", record base path), so R4
C2's "move/normalise the parenthetical" is only partly done; and `:123` says "successor of **pre-fix**
`0a1fa3a4…`" where R4 asked "amended successor of **reviewed** `0a1fa3a4…`" (the reviewed object is not a
pre-fix report).

## 4. C3 — Gate JSON / no-retry / adaptations labels: **MET** (with minor residue)

Gate JSON claim true (7 × `clear_finished`/key-false/`[]`; AR `gate_not_applicable.txt` + exclusivity
substitutes); "no U2 retry" qualified by the :9–10 disclosure; `3.225×` is labelled a cross-host composite at
`:65` (with bpb/VRAM not normalised) and `0.2345 s/request` a wall-clock surrogate at `:97`; the TASL-2
substitution list is complete (`:78–80`), the 17 Nov Ada un-isolated U2 is named at `:65`. Residue (MINOR m2):
the Blocked section (`:96–97`) still says "the earlier Ada attempt"/"vs Ada 67.901 s" without naming the 17 Nov
un-isolated U2, and `3.225×` there is not labelled a composite (only "cross-host option-A slowdown").

## 5. C4 — Record cell / licence / host caveat: **PARTIAL**

- **Record cell:** captures directory + `7,055/7,055 OK` + `SHA256SUMS 32f5009a…` present (`:23`) ✅. Missing:
  the smoke result sha `8814eecc…` beside the record (only in the citations `:127`) — R4 C4 residual.
- **Licence/availability cell:** still "autoresearch README-MIT / climbmix MIT-claimed, no LICENSE file; data
  available; option A CPU transport". The README-MIT/no-LICENSE and "MIT-claimed" (uploader assertion) parts are
  right, but availability is not stated to the U1 §7 level (public/HTTP 200, data present, **963 M**, manifest
  `ab7186d2…` — the manifest is in the data column), and "option A CPU transport" is methodology in a
  licence/availability cell (R3 m8/R4 C4).
- **Host caveat:** census `:114–115` correctly says CUDA IPC is not tested, the AR row uses option A's CPU memfd
  path only, and no `cuda_share`/`cuda_open` node is covered; sidecar `:8`/`:10` add "both option-A host gates,
  not §3 item-7 CUDA-IPC passes" and "no CUDA IPC claim". Still not stated: "TASL-2 host checks PASS for the AR
  option-A gate only" (census) and `HARNESS_ISOLATION` §5 item 5/§5.5 **open** (the sidecar's "not §3 item-7"
  wording conveys the gate scope but not the §5 item-5/§5.5 status).

## 6. C5 — Revision binding and evidence: **NOT MET** (binding sha fixed; chain figure wrong; R5 carry not recorded; uncommitted)

R4 C5 required: (i) name the current revision sha, (ii) record `79ad29ca…` as the R3-accepted predecessor with
the net delta, (iii) remove the duplicated fix-review occurrence, (iv) record R5's carried conditions
open/closed, (v) qualify "All eight rows are complete"; and commit the census with the cited AR evidence.

- **(i) Binding: fixed, and correctly designed.** The sidecar binds the exact census sha `ef001f89…`, which
  rehashes the current file; the census defers to the sidecar as the binding record (the only sound way to avoid
  a document containing its own hash). ✅
- **(ii) Net delta: wrong.** Census `:135–136` and sidecar `:6` state "R3 object `79ad29ca…` (123 lines /
  12,634 B) → current, **+13 lines / +1,350 B**". The current object is **139 lines / 14,565 B**, so the true
  R3→current delta is **+16 lines / +1,931 B**. The recorded `+13/+1,350` is exactly the R3→R4-object step
  (136 lines / 13,984 B); the R4→current step itself is +3 lines / +581 B, which the pair records nowhere. Since
  the R3 bytes are not preserved, the delta is the only auditable relationship in the binding record, and it is
  false. ❌
- **(iii) Duplicate fix-review: fixed.** ✅ (one occurrence, `:86`).
- **(iv) R5 carried conditions: not recorded.** R4 C5(iv) required the census to record R5's carried conditions
  open/closed. Neither the census nor the sidecar records any R5-condition disposition; several are visibly still
  open: R5 C7 (the verbatim mandated imdb sentence is still a paraphrase at
  `:57–58` with the self-referential "the census/paper appendix must carry this disclosure"), R5 C8
  ("whole-smoke CPU/RAM aggregates labelled" at `:46` still overstates what the census carries — RAM max RSS and
  a VRAM upper bound; CPU time is only in the `time -v` captures), R5 C5 (licence column partial, §5 above),
  R5 C6 (kit-update shas/U1 audit/AR code-review "0 BLOCKING" still not cited), R5 C10 (commit the AR evidence /
  state the SHA256SUMS caveat — not addressed). ❌
- **(v) "Complete": weakly qualified.** `:107` says "All eight rows are complete in the census sense"; the
  header carries ENGINEERING_ONLY and `:66` notes the review is conditional on C1–C5, but R4's requested
  qualification (U2-review conditional C1–C5 or ENGINEERING_ONLY raw-cost status) is not stated in the
  completion sentence. Partly.
- **Commit/preserve: not done.** The census is tracked-modified, the sidecar and all AR evidence are untracked,
  and no commit exists (only the 109-line HEAD blob). R4 C5's commit requirement is still outstanding; sidecar
  `:5` says "pending commit with this sidecar".

---

## 7. Findings

| # | severity | where | finding |
|---|---|---|---|
| **MAJOR-1** | **MAJOR (record-only; C1, before-commit)** | census `:126–127`, `:138–139`; sidecar `:7`; U2 result `:71–72` | U2 result traceability still wrong/incomplete. The `+6 lines/+280 B` figure is attributed to "reviewed→current" but is the `c03f0cbd→ee21f6d9` step; reviewed→current is **+16 lines/+1,591 B** (`ca3bcadd` 57/3,893 → `ee21f6d9` 73/5,484). The intermediate chain (`8430854c` 67/5,181; `c03f0cbd` 67/5,204, +23 B parent-peak) is omitted; sibling's 74-line size, the open U2-review C3/C4 residual list and the preservation location of the signed `R1-TRACKG-AR-U2-TASL2` are still missing. The U2 result's own revision note still says reviewed `8430854c…`/current `c03f0cbd…`, contradicting the census/sidecar and still false. No measured value is affected. |
| **MAJOR-2** | **MAJOR (record-only; C5)** | census `:135–136`; sidecar `:5–6` | The binding record's chain figure is false: R3 `79ad29ca…` (123/12,634) → current (139/14,565) is **+16 lines/+1,931 B**, not the recorded **+13 lines/+1,350 B** (that is the R3→R4-object step; R4→current +3/+581 is unrecorded). Because the R3 bytes are not preserved, this is the only recorded chain relation and it is wrong. The sidecar also overclaims "this revision applies R4's C1–C5" (C1 is not applied, C5 partly) and misdescribes R4 as NOT ACCEPTED on "(current-sha/citations/labels)" (R4's MAJORs were C1/C2/C5; labels were MINOR m1/C3 residue). R5's carried conditions are not recorded open/closed (C5(iv)), and the pair remains uncommitted. |
| m1 | MINOR | census `:130–133`, `:123` | C2 residue: dangling stale citations fragment (duplicate result-review names, HousePrice unit/result names, "isolation fix review", record base path) left after the rewritten sentence; "successor of pre-fix `0a1fa3a4…`" should be "amended successor of reviewed `0a1fa3a4…`". |
| m2 | MINOR | census `:96–97` | C3 residue: Blocked section still says "the earlier Ada attempt"/"vs Ada 67.901 s" without naming the 17 Nov Ada un-isolated U2 (it is named at `:65`); `3.225×` there is not labelled a composite. |
| m3 | MINOR | census `:23`, `:114–115` | C4 residue: licence/availability cell lacks the U1 §7 availability facts (public/HTTP 200, data present, 963 M; manifest `ab7186d2…` is in the data column) and keeps methodology "option A CPU transport"; host caveat lacks the explicit "AR option-A gate only" and `HARNESS_ISOLATION` §5 item 5/§5.5 **open** statements (the sidecar `:8`/`:10` covers the gate-scope/CUDA-IPC caveat); smoke sha `8814eecc…` is not beside the record cell. |
| m4 | MINOR | census `:105–106` | Readiness sentence is still garbled: "the six earlier nodes, HousePrice and (after the TASL-2 clean smoke/U2) all eight are set; **review,** autoresearch joins the table" — the "review," fragment does not parse (R4 m3 open). |
| m5 | MINOR | sidecar `:7` | "C1–C4 partial residuals recorded" is unsupported: no residual list is recorded in the pair (only the reviewed-unit "recorded residual" at census `:79`); R5 C7/C8 remain visibly open without disposition. |
| m6 | MINOR | U2 result `:71–72` (cross-record; the actionable part of MAJOR-1) | The U2 result's own revision note still states reviewed `8430854c…` / current `c03f0cbd…`; current is `ee21f6d9…`, reviewed is `ca3bcadd…`. Must be edited (outside the census/sidecar) so the pair and the result cite the same objects. |
| m7 | MINOR | sidecar `:6` | The acceptance chain names accepted objects (`4e050ad2…`, `76bf88db…`, `79ad29ca…`) but not the accepting review documents' shas (seven-node R5 `9c604f1b…`, AR-row R2 `5fe423ac…`, R3 `4c5f1848…`, R4 `d4c3f9f0…`), so the chain is not self-verifiable from the binding record. |
| m8 | MINOR | census `:107`, `:66` | "All eight rows are complete in the census sense" remains a weak qualifier; R4 C5(v) asked for the U2 review's conditional C1–C5 / ENGINEERING_ONLY raw-cost status in that sentence. |
| m9 | MINOR | census `:46` | R5 C8 still open: "whole-smoke CPU/RAM aggregates labelled" overstates the content — the census carries whole-smoke max RSS (RAM) and the VRAM upper bound; CPU time is only in the captures. |
| t1 | traceability note (not a finding against a value) | — | The current object `ef001f89…` is not preserved (tracked-modified, not a git object); the sidecar and all AR evidence are untracked; earlier objects `2dbf2c16…`/`79ad29ca…`/`4e050ad2…`/`76bf88db…` are not preserved either. If this revision is edited in place again without a commit/preserved copy, it is lost like its predecessors. The sidecar must be (re)written **after** the final census edit and must state the delta recomputed at the final sha. |

**No BLOCKING was found, and no fabricated, overclaimed or altered measured value was found.** The eight rows are
unchanged and correct, the captures verify 7,055/7,055, all cited shas match the delivered files, and the census
remains an ENGINEERING_ONLY U2 raw-cost record that does not block G.1b/G.4. However the two MAJOR record-only
traceability defects above mean the pair cannot yet be accepted as the final U4 record/binding, so "no new
MAJOR/BLOCKING" **cannot** be confirmed in the record sense.

## 8. Conditions (documentation/record only — no re-run, no measurement/record edit)

- **C1 (before commit; MAJOR-1).** In the census and sidecar record the reviewed `ca3bcadd…` (57 lines / 3,893 B,
  not preserved) → `8430854c…` (67/5,181; +10 lines/+1,288 B; R2-recorded) → `c03f0cbd…` (67/5,204; +23 B
  parent-peak; R3-recorded) → current `ee21f6d9…` (73/5,484; +6 lines/+280 B unit-provenance block) chain, with the
  correct reviewed→current total (**+16 lines/+1,591 B**); replace the misattributed
  "reviewed→current +6/+280" wording; add the sibling unit's 74 lines / 6,374 B; list the open U2-review C3/C4
  residuals; record where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved (or state that it
  is not preserved and where it was delegated). Correct the U2 result's own revision note (`:71–72`) in the same
  pass.
- **C2 (before commit; MAJOR-2).** After the final census edit, recompute the R3→current delta and rewrite the
  sidecar **last** so it binds the then-final census sha and states the correct delta (today: `79ad29ca…`
  123/12,634 → `ef001f89…` 139/14,565 = **+16 lines/+1,931 B**; if the file changes, recompute). Record the R5
  carried conditions C4–C10 open/closed (at least C5 licence, C6 shas, C7 imdb verbatim, C8 CPU wording, C9
  binding, C10 AR-evidence commit) and correct the "applies R4's C1–C5"/"current-sha/citations/labels"
  descriptions. Add the accepting review shas to the chain for self-verifiability.
- **C3.** Remove the dangling citations fragment at `:130–133` and normalise the parenthetical; fix the garbled
  readiness sentence at `:105–106`; name the 17 Nov Ada un-isolated U2 in the Blocked section; change "pre-fix"
  to "amended successor of reviewed `0a1fa3a4…`".
- **C4.** Complete the licence/availability cell per U1 §7 (963 M, HF revision, public/HTTP-200 availability;
  manifest already in the data column) and drop the methodology text from that cell; add "AR option-A gate only"
  and `HARNESS_ISOLATION` §5 item 5/§5.5 **open** to the host caveat; put the smoke sha `8814eecc…` beside the
  record.
- **C5.** Commit the final census **with** the sidecar and the cited AR evidence (U2 result, unit sibling, host
  reports/reviews, smoke + captures) and preserve the accepted revision; after committing, re-run
  `shasum -a 256 -c SHA256SUMS` (R5 C10) and verify the sidecar sha still matches. Any further content edit
  invalidates the sidecar binding and needs a fresh binding (and, if more than the delta/sha lines change, a fresh
  review).

## 9. Acceptance binding and read-only attestation

This review binds to the pair: census
`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`ef001f890b29c2b8c75e072556f1172562a874726a4d3378604e1567e3e3308e`**, 139 lines / 14,565 bytes, mtime
2026-11-21T04:25:41Z, tracked-modified at HEAD `ebe03cd5` (HEAD blob `146b1114…`); and sidecar
`TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md`, SHA-256
**`f5c781d4ccc69e3cf520ee6e1e2461cb4d6b36e5208c45ff58e74b7c90963a48`**, 10 lines / 2,207 bytes, untracked.
The verdict is **NOT ACCEPTED**: measured content, captures and citations are correct and unchanged, but R4's C1
is not closed and C5 is only partly closed (the two recorded traceability deltas are wrong, the U2 chain/items are
incomplete, the U2 result's own note still contradicts the pair, and R5's carried conditions are not recorded).
The next revision must preserve a snapshot (commit) because this object `ef001f89…` is otherwise lost in place
like `79ad29ca…`, `2dbf2c16…` and `4e050ad2…` were, and the sidecar must be written after the final census edit
with the delta recomputed at the final sha.

**Written:** only this review file. **Read-only:** all cited files, captures and records; `shasum -a 256`;
`shasum -a 256 -c` (captures 7,055/7,055 OK, rc 0); JSON re-parses of all seven earlier gate JSONs and all nine AR
run records; `pandoc -f gfm` render check (rc 0); `git rev-parse/status/log/show/ls-tree/diff`; `wc`, `stat`,
`grep`, `diff`, `cat`. **Not done:** no run, smoke, U2/GPU/T1/census job, probe, SSH/live-host inspection, edit
outside this review, commit, push, deletion/move, HTCondor/deepthought action, or secret/credential read. No other
review's object was modified. This is the AR-row review round 5; it is distinct from the seven-node census review
`TRACKG_U4_CENSUS_REVIEW_R5_20261120.md`.
