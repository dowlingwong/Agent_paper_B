# Independent final review (round 4) — Track G U4 census AR-row update after R3 conditional acceptance (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer-r4`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2/TASL-7 host checks, the AR unit/result/smoke, the U4 census, or the
earlier U4 reviews (R1–R5 and the round-1/round-2/round-3 AR-row reviews). **Read-only:** the only file written is
this review (untracked; no commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or live-host contact,
edit of any other file, deletion/move, HTCondor or deepthought action. Every fact below is recomputed from the
delivered local bytes or read from local git/records. (`shasum -a 256 -c` over the delivered AR capture bundle is a
read-only integrity check, not an experiment run.)

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`2dbf2c16c6292868e0cac7ebc690af640c95638ead33ba0f6d12b8b56138b448`**, **136 lines / 13,984 bytes**, mtime
**2026-11-21T04:17:39Z**, **tracked and modified** in the worktree at HEAD **`ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`**
(`origin/ops-tasl-20261116` = same; `origin/main` = `4aac52092813b2b01ddb96cd7d135c390aeff645`). The HEAD blob is
`6d1ac47f…` = SHA-256 `146b111410122108c7efa25246b61db62060adcaa3ea14fb2111ec2e13d692d7` (109 lines), i.e. the
R5-accepted/C1-repaired census committed at `76f1d7ba`; the working-tree delta vs HEAD is **+55/−28 lines**
(title; header/STOP disclosure; AR row; run-level AR row; gate-JSON and Paper-A sentences; per-suite autoresearch
bullet; new "AR row measurement notes" paragraph; Blocked/readiness text; citations; revision line). The seven
earlier rows and their run-level rows are byte-identical to the HEAD blob, as are the MLAgentBench/MLGym funnel
bullets, kitchen/environment and the licence paragraph.

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_R3_20261121.md` SHA-256
**`4c5f18483dd6c50a3a112a9f19b67274f63ba6055bf2ae8c5851c8259465e31c`** (292 lines / 26,580 B, mtime 04:17:09Z) —
**ACCEPTED, 0 BLOCKING, 0 MAJOR, 11 MINOR, 1 traceability note, conditions C1–C5**, with C1/C2 marked before-commit.
Its object, SHA-256 **`79ad29caf56805cff375ef04dfed897b21ecc2b92c7d2a6a289be9479ebc7f26`** (123 lines / 12,634 B,
mtime 04:10:14Z), is **not preserved**: no worktree file matches, no git object of 12,634 B rehashes to it, and only
the R3 review's verbatim quotes record it. The R3→R4 delta is therefore **+13 lines / +1,350 B net** and is not
byte-auditable — traceability note **t1**.

**Inputs / authority read (all local, read-only; no live host was contacted).** The AR U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` **`ee21f6d9e8bb3fd807809c54cdfb039ff1643c07f7950b88e5e5a770bb480be4`**,
73 lines / 5,484 B, mtime **04:17:39Z**, untracked (R3 recorded the then-current `c03f0cbd…`, 67 lines / 5,204 B;
that object is not preserved; the U2 review's object `ca3bcadd…`, 57 lines / 3,893 B, and R2's recorded
`8430854c…`, 67 lines / 5,181 B, are also not preserved); the executed-unit sibling copy
`U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` **`b83d91597eaf665b942f4f02fd30f149da53f5f1cc0e6579d1e6711669734432`**
(74 lines / 6,374 B, `diff` byte-identical to the committed Ada-targeted unit `…UNIT_20261121.md` at commit
`d65079af`, not in the captures); the smoke result `TASL2_AR_COND7A_RESULT_20261121.md`
**`8814eecc1fb0f9ded4920adc15aa276a05c08e5a181a0a1ed4c5d564f088d0ad`** (288 lines / 22,667 B, PASS); its captures
`TASL2_AR_COND7A_RESULT_20261121_captures/` — `SHA256SUMS` **`32f5009a347264bb1d820c420dedeaf0d2dd5fe8822516597f1bba53a3ca0aeb`**,
**7,055 entries**, **7,056 regular files**, `shasum -a 256 -c` → **rc 0, 7,055/7,055 OK**; the U2 result review
`U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` **`9de24ec5ebd38825b4f352deeeb7df6a9b5f2d0d1890258119bc2368b4c16aaa`**
(212 lines, **ACCEPTED — 0 BLOCKING, 1 MAJOR report-only, 12 MINOR, conditional on C1–C5**); the TASL-2 host-check
report **`83636c039fcb7d503abb15468cf4588ebd6795588012b44f6d8f79470d7a5bb6`** / review
**`bfe9b2312d7483e54ea8692544d4cf434c093616d0c4abc2cc09a1db214e0efd`** (ACCEPTED, C1–C4); the TASL-7 host-check
report **`2b703226e6aec430df24b3333ed002940023c99aa8d535392e117aa4b40f2abf`** / review
**`18e261cd3641d3ec370599c8f38131862ef8c3e5e1b92659f08c984202fa15d5`** (ACCEPTED, C1–C4); the superseded addendum
`TRACKG_U4_CENSUS_ADDENDUM_20261121.md` **`fa7bb75def3dde69c998374a4563bdc876489f3899e4c24f73c8486bb25022ef`**; the
isolation fix report **`0ff9a7f2f4e6631cc952c573f68f0bf18d79a7993b9f2bb1a33e6ce17786cd43`** / review
**`c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`**; R5 review
**`9c604f1b1220652cb3ccc109e0d85863b6a9e34ac02237b5ff57070fc3cc6b91`**; `docs/r1/PLAN.md` at HEAD
**`7e0e160a3cc4aaa47be8f941a4c5840b16d700b47fa2568a0d989e6113e6b180`** (1,337 lines; `R1-TRACKG-AR-COND7` :1317,
`R1-T1-HOST-H200` :1329, `R1-TRACKG-G3-EARLY` :1330 all verified present); the seven earlier record directories and
their gate JSONs; and the AR captures parsed directly (9 `run_record.json` = 8 executed + refused `s001`;
`gate/gate_not_applicable.txt`; `SHA256SUMS`). The census was cell-counted (8 data rows × 15 cells main table, 8 × 5
run-level table).

**Verdict: NOT ACCEPTED — 0 BLOCKING, 3 MAJOR (record/traceability only), 4 MINOR, 1 traceability note.** The measured
content is unchanged and correct (all eight rows/values verified; captures 7,055/7,055 OK; no fabricated or
overclaimed value; U4 still does not block G.1b/G.4), but the five carried conditions C1–C5 are **not closed**:
**C1, C2 (the two R3 marked before-commit) and C5 are unmet; C3 and C4 are partial.** In particular, the census's
acceptance/revision line binds the **wrong census sha** (`79ad29ca…` described as "this census revision", while the
file is `2dbf2c16…`) and cites a **superseded U2 result sha** (`c03f0cbd…`, current `ee21f6d9…`). Because the
acceptance binding itself is wrong, this revision cannot be taken as the final U4 record.

---

## 1. Confirmations that do hold (measured content unchanged; U4 readiness unchanged)

- **Seven earlier rows unchanged.** The main-table rows 1–7 and run-level rows 1–7 are **byte-identical** to the
  R5-accepted HEAD blob `146b1114…` (verified by extracting the table rows from `git show HEAD:…` and from the
  worktree and `diff`-ing: the only difference is the added AR row). Their seven record directories and gate JSONs
  exist and re-parse as `verdict:"clear_finished"`, `paper_a_live_waiting_for_card:false`,
  `evidence.gpu.paper_a_processes:[]` (all seven checked). Their measured values are therefore unchanged and remain
  covered by R5.
- **AR row values unchanged.** All 15 cells re-checked against the R3-verified values: B1 `218.951 s` /
  `1.293937 (val_bpb)`, B2 `218.443 s` / `1.293937`, sealed `n/a`, timeout `656.853 s` (= 3 × 218.951),
  upper bound `12,436 MiB`, `GPU-4d623e76…` (TASL-2 4090) cpus 0-7, committed pin `147f0d35…`, manifest
  `ab7186d2…`. The only change in this row is **metadata**: the record cell now adds
  `(captures SHA256SUMS 32f5009a…)` — exactly the C4 target — and the row itself is the new eighth row. No measured
  value changed. The run-level AR row (`3,204,520` kB; `ca049086…`; gate path
  `…_captures/gate/gate_not_applicable.txt`; disk `388,531,040,256 → 388,344,332,288 B`) and the AR measurement notes
  (`1,791.0 s`, `3.176×`, `1,980.1 MB`, `3,720.4 MB`, `6,560.3 MB`, `5.17 GiB`, `12,436 MiB`, memfd/no CUDA IPC,
  pins 20/21) all equal the R3-verified values.
- **Captures unchanged.** `SHA256SUMS` sha **`32f5009a…`** (same as R3), 7,055 entries, 7,056 regular files,
  `shasum -a 256 -c` → **rc 0, 7,055/7,055 OK**; captures directory/`SHA256SUMS` mtimes 03:34–03:35Z (before R3's
  review); no capture was edited.
- **No new measurement/record edit, no re-run.** The clean single smoke remains the only U2 run; one executed smoke,
  no second U2; `CHECKLIST_E_PASSED`; ENGINEERING_ONLY raw-cost row (not T1 evidence).
- **U4 no longer blocks G.1b/G.4 — confirmed.** `R1-TRACKG-G3-EARLY` (`PLAN:1330`) sets the six earlier nodes for
  G.1b/G.4 now and lets HousePrice/autoresearch join as soon as their U2 passes; `R1-T1-HOST-H200` (`PLAN:1329`)
  keeps the T1 labels on H200. The census readiness text says the census does not block G.1b/G.4 and is not evidence;
  that is correct. (The census does **not cite** those two authority rows — see C2.)

## 2. C1 — U2 result sha/delta/unit nuance: **NOT MET (stale sha; mislabelled reviewed object)**

R3 C1 required the census to record the **current** U2 result sha, its delta history, and the executed-unit nuance.

- **Stale current sha.** The census cites `U2_ISO_AUTORESEARCH_RESULT_20261121.md` sha **`c03f0cbd…`** at `:125` and
  repeats it in the revision line `:134` ("the U2 result was `c03f0cbd…` after the parent-peak text addition"). The
  current file is **`ee21f6d9…`, 73 lines / 5,484 B, mtime 04:17:39Z** — i.e. **+6 lines / +280 B** after the
  `c03f0cbd` state (67 lines / 5,204 B). The added block is `:10–15` of the U2 result: the executed-unit provenance
  record (reviewed unit `3bb015a1…`; amended unit preserved as the sibling `b83d9159…`; TASL-2 adaptations; single
  smoke as U2 measurement) — exactly the U2-review C1/MAJOR-1 close. The census records neither the current sha nor
  this +280 B delta, so its C1 record is stale.
- **Mislabelled "prior reviewed" sha.** `:134` calls `8430854c…` the "prior reviewed" object. The U2 review's object
  was **`ca3bcadd…`** (57 lines / 3,893 B, not preserved; U2 review `:14`; R1 review `:23`/`:244`); `8430854c…`
  (67 lines / 5,181 B) was **R2's then-current recording** (R3 `:29`), not the reviewed object. `ca3bcadd…` is
  absent from the census entirely, so the required three-step chain
  `ca3bcadd → 8430854c → c03f0cbd → ee21f6d9` is not recorded and the one link that is recorded is mislabelled.
- **Unit nuance: partially recorded.** The census now correctly says the sibling `b83d9159…` is **byte-identical to
  the committed Ada-targeted unit** and **not in the 7,055-entry captures**, with reviewed `3bb015a1…` not preserved
  (`:135–136`) — this closes R3 m1 in substance. Still missing: the sibling's **74 lines**; the **list of open
  U2-review C3/C4 residuals**; and **where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved**.
- **Cross-record consequence.** The U2 result's own revision note (`:71–72`) still says its current sha is
  `c03f0cbd…`; that is now false (`ee21f6d9…`). The census cannot cite a coherent "current" U2 sha until the U2
  result's note is corrected (or the census cites `ee21f6d9…` and records the two-step delta explicitly).

## 3. C2 — citation completeness: **NOT MET (host-checks fixed; authority rows and review count still wrong)**

R3 C2 required: host-check report/review shas; AR result/smoke/captures; `R1-TRACKG-AR-COND7` (`PLAN:1317`) and
`R1-T1-HOST-H200` (`PLAN:1329`); and a fix of the result-review count/phrasing.

- **Fixed:** TASL-2 host-check report `83636c03…` + review `bfe9b231…` and TASL-7 report `2b703226…` + review
  `18e261cd…` are now named correctly and the files' sha256 match. AR smoke `8814eecc…`, captures `32f5009a…` and
  U2 review `9de24ec5…` are cited correctly.
- **Not fixed — stale AR result sha:** `:125` cites the AR U2 result at `c03f0cbd…` (current `ee21f6d9…`; see §2).
- **Not fixed — authority rows missing:** `R1-TRACKG-AR-COND7` is **absent from the census entirely** (neither body
  nor citations); `R1-T1-HOST-H200` appears only in the body at `:108`, not in the citations with its `PLAN:1329`
  locator. Both rows exist at HEAD (verified `:1317`, `:1329`).
- **Not fixed — result-review count/phrasing:** `:120–121` still says "**three** result reviews covering the six
  earlier torch nodes + HousePrice result review + AR U2 result review". Only **two** reviews cover the six torch
  nodes (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` `965dc993…` five nodes + `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`
  `d4cdd9bb…` one node); the third is `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` (`b2c463a7…`), so
  "+ HousePrice result review" **double-counts** — the exact R3 m3/C2 defect. The parenthetical naming the two
  result-review files is also misplaced *after* the AR-captures sentence (`:126–127`), breaking the sentence.
- **Not fixed:** the amended TASL-2 host-check report `83636c03…` is not recorded as the successor of the reviewed
  `0a1fa3a4…` (R3 C2/C4).

## 4. C3 — gate JSON / no-retry / adaptations labels: **PARTIAL**

- **Gate JSON — fixed and now correct:** `:39–40` says "the seven torch rows' gate JSONs are `clear_finished`, key
  false, paper_a_processes [], captured with UTC; the AR row is on TASL-2, has no Paper A, and records
  `gate_not_applicable.txt` plus exclusivity controls". Verified: all seven earlier gate JSONs re-parse
  `clear_finished`/key false/`paper_a_processes []`; the AR capture `gate/gate_not_applicable.txt` reads
  `paper_a_gate=NOT_APPLICABLE_ON_TASL2` with the exclusivity substitutes. ✅
- **No-retry — partially qualified:** the header is now "one executed smoke; no U2 retry" (`:7`) with the 20 Nov /
  21 Nov STOP disclosure (`:9–10`). But the "All eight rows: one unit, one executed smoke, **no retry**" sentence
  (`:43`) is still unqualified — R3 m5's second statement. ❌ (minor)
- **Substitutions — fixed in the notes:** the full TASL-2 substitution list is present (`:78–80`: host TASL-2, env
  `ar-cond7a`, data root `/home/dowling/r1_trackp/data`, 20,000 MiB floor, no Paper A gate), the 17 Nov Ada
  **un-isolated** baseline is named at `:66`, and "cross-host" is used at `:66`/`:98`. ✅
- **Composite/surrogate labels — still missing:** `3.225×` is not labelled a **composite** (option A + host change;
  bpb/VRAM not normalised) — "cross-host option-A" is close but not the required label — and `0.2345 s/request` is
  not labelled a **wall-clock surrogate** (`:66–67`, `:97–98`). The U2 result now states "bpb/VRAM not normalised"
  (`:63–64`), but the census text does not. ❌
- The Blocked section still says "the earlier Ada attempt" (`:97`) rather than the 17 Nov un-isolated U2 (minor;
  `:66` gets it right).

## 5. C4 — record cell / licence / host caveat: **PARTIAL**

- **Record cell — partly fixed:** `:23` now carries `(captures SHA256SUMS 32f5009a…)` ✅. Missing: the captures
  **directory** name and the **7,055/7,055 OK** verification count (R3 C4 asked for both), and the smoke result sha
  in the same cell (it is in the citations).
- **Licence/availability cell — NOT fixed:** `:23` still ends "autoresearch MIT/climbmix MIT-claimed; option A CPU
  transport" — unchanged from the R3 object. Per U1 §7 this needs the code licence status (MIT declared in the
  README, **no LICENSE file**), the climbmix MIT **uploader assertion** on the HF card, and availability
  (public/HTTP 200, data present, 963 M, manifest `ab7186d2…`); "option A CPU transport" is methodology, not
  licence/availability (R3 m8). ❌
- **Host caveat — partly fixed:** the new paragraph `:114–116` says CUDA IPC is not tested, the AR row uses option
  A's CPU memfd path only, and no `cuda_share`/`cuda_open` node is covered by this census ✅. Missing: "TASL-2 host
  checks PASS **for the AR option-A gate only**"; `HARNESS_ISOLATION` §5 item 5/§5.5 **open**; the amended
  `83636c03…` report as successor of the reviewed `0a1fa3a4…`. ❌ (partial)

## 6. C5 — revision line binds current sha and evidence: **NOT MET (binds the wrong census sha)**

- **Wrong self-binding.** `:132–133` reads "Revision/acceptance line (21 Nov): **this census revision sha
  `79ad29ca…`** is the object accepted by U4 AR-row review R3 …". The file's actual sha is **`2dbf2c16…`** (136
  lines / 13,984 B); `79ad29ca…` was the R3 object (123 lines / 12,634 B) and those bytes are **not preserved**. The
  statement is therefore false about the current document, and the census nowhere records its own current sha
  `2dbf2c16…` or the `79ad29ca → 2dbf2c16` net delta (+13 lines / +1,350 B). Acceptance cannot bind to it. ❌
- **Duplicate fix-review filename still present.** `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` is listed twice
  (`:86` and again at the start of `:87`) — R5's C4/m4 item, still open, and R3 C5 explicitly required its removal.
  ❌
- **R5's carried conditions not recorded** open/closed: duplicate fix-review name (R5 C4); licence column (R5 C5);
  citations (R5 C6); the verbatim imdb disclosure sentence (R5 C7); whole-smoke CPU/RAM wording (R5 C8); revision
  binding/preserve (R5 C9); commit AR evidence (R5 C10). ❌ (R3 §6/m10, C5)
- **"All eight rows are complete" not qualified.** `:108` states completion without the U2 review's conditional
  C1–C5 or the ENGINEERING_ONLY raw-cost status (only "is not evidence" follows). ❌ (R3 m11)
- **Commit/preserve still not done.** The census is still tracked-modified, the AR evidence files are untracked, and
  no commit exists; the R3-accepted object was overwritten in place (again). R3 C5 required committing the census
  together with the cited AR evidence and preserving the accepted revision.

---

## 7. Findings

| # | severity | where | finding |
|---|---|---|---|
| **MAJOR-1** | **MAJOR (record-only; C1, before-commit)** | census `:125`, `:134–135`; U2 result `:71–72` | U2 result traceability is stale/mislabelled: cites `c03f0cbd…` (67/5,204) while the current result is `ee21f6d9…` (73/5,484, +6 lines/+280 B, unit-provenance block closing U2-review C1/MAJOR-1); calls `8430854c…` "prior reviewed" (the reviewed object was `ca3bcadd…`, 57/3,893, not preserved); omits `ca3bcadd…`, the +280 B delta, the 74-line sibling size, the open U2-review C3/C4 residual list and where `R1-TRACKG-AR-U2-TASL2` is preserved. The U2 result's own revision note is now false. No measured value is affected. |
| **MAJOR-2** | **MAJOR (record-only; C2, before-commit)** | census `:118–130` | Citations incomplete: `R1-TRACKG-AR-COND7` (PLAN:1317) absent; `R1-T1-HOST-H200` (PLAN:1329) not in the citations; AR U2 result sha stale (`c03f0cbd…`); "three result reviews covering the six earlier torch nodes + HousePrice result review" still double-counts (two reviews cover the six torch nodes; the third is the HousePrice review; the AR review is a fourth); the result-review parenthetical is misplaced and names only two files; the amended host report `83636c03…` is not recorded as successor of reviewed `0a1fa3a4…`. |
| **MAJOR-3** | **MAJOR (record-only; C5)** | census `:132–136`, `:86–87`, `:108` | The revision/acceptance line binds the **wrong census sha**: describes `79ad29ca…` as "this census revision" while the object is `2dbf2c16…`; no current-sha binding or `79ad29ca→2dbf2c16` delta; the R3 object's bytes are not preserved. Also: duplicated `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (`:86`/`:87`) still present (R5 C4 open); R5's carried conditions not recorded; "All eight rows are complete" unqualified; census + cited AR evidence still uncommitted. |
| m1 | MINOR | census `:43`, `:66–67`, `:97–98` | C3 residue: `:43` "no retry" unqualified (the header `:7`/`:9–10` is qualified); `3.225×` not labelled a cross-host composite (option A + host change, bpb/VRAM not normalised); `0.2345 s/request` not labelled a wall-clock surrogate; Blocked section says "the earlier Ada attempt" instead of the 17 Nov un-isolated U2. |
| m2 | MINOR | census `:23`, `:93–94`, `:114–116` | C4 residue: record cell lacks the captures directory name and 7,055/7,055 OK count; licence/availability cell unchanged (no README-MIT/no-LICENSE-file note, no climbmix uploader-assertion, no availability/data-present 963 M/`ab7186d2…`); host caveat lacks "AR option-A gate only", `HARNESS_ISOLATION` §5 item 5/§5.5 open, amended `83636c03…` successor note. |
| m3 | MINOR | census `:106–107` (new in this revision) | The readiness sentence was garbled by the edit: "the six earlier nodes, HousePrice and (after the TASL-2 clean smoke/U2) all eight are set; review, autoresearch joins the table …" — the "review," fragment and the tri-part subject do not parse; rewrite. |
| m4 | MINOR | U2 result §Revision note `:71–72` (cross-record) | The U2 result still states its current sha is `c03f0cbd…`; it is `ee21f6d9…`. Must be corrected (and the c03f0cbd→ee21f6d9 delta recorded) so the census and the result cite the same object. |
| t1 | traceability note (not a finding against a value) | — | The R3 object `79ad29ca…` was overwritten in place and is not preserved (no file/git blob); the R3→R4 delta is auditable only against R3's verbatim quotes. The census remains uncommitted, so this review's object `2dbf2c16…` is also not preserved unless a snapshot is committed. Preserve the accepted revision and its AR evidence on commit. |

**No new BLOCKING was found, and no fabricated, overclaimed or altered measured value was found.** The eight rows are
unchanged and correct, the captures verify 7,055/7,055, and the census remains an ENGINEERING_ONLY U2 raw-cost record
that does not block G.1b/G.4. However, the three MAJOR items above are **new record-only defects introduced/left open
by the C1–C5 fix pass** (the acceptance line binds the wrong sha; the U2-result sha chain is stale; the before-commit
citation/authority items are missing), so this reviewer cannot confirm "no new MAJOR/BLOCKING" in the record sense.

## 8. Conditions (documentation/record only — no re-run, no measurement/record edit)

- **C1 (before commit; MAJOR-1).** Record the **current** U2 result sha `ee21f6d9…` (73 lines / 5,484 B), the full
  chain `ca3bcadd…` (reviewed, 57/3,893, not preserved) → `8430854c…` (R2-recorded, 67/5,181) → `c03f0cbd…`
  (67/5,204, +23 B parent-peak, not preserved) → `ee21f6d9…` (+280 B / +6 lines, unit-provenance block closing
  U2-review C1/MAJOR-1); fix the "prior reviewed `8430854c…`" mislabel; add the sibling's 74-line size; list the open
  U2-review C3/C4 residuals; record where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved.
  Correct the U2 result's own revision note to match.
- **C2 (before commit; MAJOR-2).** Cite `R1-TRACKG-AR-COND7` (`PLAN:1317`) and `R1-T1-HOST-H200` (`PLAN:1329`);
  cite the AR U2 result at `ee21f6d9…`; rewrite the result-review sentence as two reviews covering the six torch
  nodes (`965dc993…` five-node + `d4cdd9bb…` Breakout) + the HousePrice result review (`b2c463a7…`) + the AR U2
  result review (`9de24ec5…`), and move/normalise the parenthetical; record `83636c03…` as the amended successor of
  reviewed `0a1fa3a4…`.
- **C3.** Qualify `:43` "no retry" (or cross-reference `:9–10`); label `3.225×` a **cross-host composite** (option A
  + host change; bpb/VRAM not normalised) and `0.2345 s/request` a **wall-clock surrogate**; name the 17 Nov Ada
  un-isolated U2 in the Blocked section.
- **C4.** Put the captures directory + `SHA256SUMS` `32f5009a…` + 7,055/7,055 OK and the smoke `8814eecc…` beside
  the record; complete the licence/availability cell per U1 §7; extend the host caveat with "AR option-A gate only",
  §5 item 5/§5.5 open, and the amended-report successor note.
- **C5.** Rewrite the revision/acceptance line to: (i) name the current revision sha (`2dbf2c16…` now; the sha at
  commit after the next edit), (ii) record `79ad29ca…` (123/12,634, bytes not preserved) as the R3-accepted
  predecessor with the net `+13 lines / +1,350 B` delta, (iii) remove the duplicated
  `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` occurrence, (iv) record R5's carried conditions open/closed, and
  (v) qualify "All eight rows are complete". Commit the census with the cited AR evidence and preserve the
  R4-accepted revision.

## 9. Acceptance binding and read-only attestation

This review binds to the reviewed content
`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`2dbf2c16c6292868e0cac7ebc690af640c95638ead33ba0f6d12b8b56138b448`**, 136 lines / 13,984 bytes, mtime
2026-11-21T04:17:39Z, tracked-modified at HEAD `ebe03cd5` (HEAD blob `6d1ac47f…` = `146b1114…`, preserved). The
verdict is **NOT ACCEPTED**: R3's conditions C1, C2 and C5 are not closed and C3/C4 are partial, so the revision
cannot be taken as the final U4 record; the measured content (all eight rows, run-level facts and captures) is
unchanged, correct and unaffected. The next revision must preserve a snapshot (commit) because this object
`2dbf2c16…` will otherwise be overwritten in place like `79ad29ca…` was.

**Written:** only this review file. **Read-only:** all cited files and captures; `shasum -a 256`; `shasum -a 256 -c`
(captures 7,055/7,055 OK, rc 0); JSON re-parses of all seven earlier gate JSONs and the AR gate capture; `git
rev-parse/status/log/show/diff`; `wc`, `stat`, `grep`, `diff`, `cat`. **Not done:** no run, smoke, U2/GPU/T1/census
job, probe, SSH/live-host inspection, edit outside this review, commit, push, deletion/move, HTCondor/deepthought
action, or secret/credential read. No other review's object was modified.
