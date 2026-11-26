# Independent final review (round 6) — Track G U4 census AR-row update and binding sidecar after R5 NOT ACCEPTED (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer-r6`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2/TASL-7 host checks, the AR unit/result/smoke, the U4 census, the
binding sidecar, or any earlier U4 review (seven-node R1–R5; AR-row R1–R5). **Read-only:** the only file written
in the workspace is this review (untracked; no commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or
live-host contact, edit of any other file, deletion/move, HTCondor or deepthought action. Every fact below is
recomputed from the delivered local bytes or read from local git/records. (`shasum -a 256 -c` over the delivered
AR capture bundle is a read-only integrity check, not an experiment run; its output was captured to a system
temporary file outside the workspace.)

**Objects under review (the pair).**

| object | SHA-256 | size | mtime | git state |
|---|---|---|---|---|
| census `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md` | **`26a306732d36b024fe3eb143579138b4357dfe322d10ffc49c4ad0dfd8e1fc01`** | **140 lines / 15,045 bytes** | **2026-11-21T04:36:27Z** | **tracked-modified**; HEAD **`ebe03cd5`** = `origin/ops-tasl-20261116`; `origin/main` `4aac5209`; HEAD blob `146b1114…` (109 lines / 10,925 B); diff vs HEAD **+65/−34 lines** |
| binding sidecar `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md` | **`4880b3a039f1ff22927c2df5162070f41e7da274289b8c9fa6412b0e9e3f8c05`** | **12 lines / 2,618 bytes** | **2026-11-21T04:36:34Z** | **untracked** (`??`); binds the census sha `26a30673…` exactly |

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_R5_20261121.md`, SHA-256
**`8737edf4fedb752b01438a00d46bc8bbfda1c8b3ba4923a0e4abe50745af1153`** (275 lines / 27,833 B, mtime
04:35:47Z) — **NOT ACCEPTED, 0 BLOCKING, 2 MAJOR (record-only traceability: wrong deltas/U2 chain, uncommitted
preservation), 9 MINOR, 1 traceability note**. Its object (census `ef001f89…`, 139 lines / 14,565 B, mtime
04:25:41Z) and its sidecar (`f5c781d4…`, 10 lines / 2,207 B) are **not preserved**: no working-tree copy and no
git object. The R4 object (`2dbf2c16…`, 136 lines / 13,984 B), the R3 object (`79ad29ca…`, 123 lines / 12,634 B)
and the seven-node R5 object (`4e050ad2…`, 109 lines / 11,207 B) are likewise not preserved; only the HEAD blob
`146b1114…` is in git.

**Inputs / authority read (all local, read-only; no live host was contacted).** U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` **`86bdd42965c283ff1fe322f98a94c6fd2feed1bd5d68c309ff82a4486a1a3d81`**
(76 lines / 5,841 B, mtime 04:36:27Z, untracked); its review `U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md`
**`9de24ec5…`** (ACCEPTED, conditional C1–C5; reviewed object `ca3bcadd…` = 57 lines / 3,893 B, not preserved);
executed-unit sibling `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` **`b83d9159…`** (74 lines / 6,374 B, verified
byte-identical to the unit committed at `d65079af`); smoke `TASL2_AR_COND7A_RESULT_20261121.md`
**`8814eecc…`** (288 lines / 22,667 B, PASS); its captures `TASL2_AR_COND7A_RESULT_20261121_captures/` —
`SHA256SUMS` **`32f5009a…`**, **7,055 entries**, **7,056 regular files**, 17 symlinks, 2,128 dirs,
`shasum -a 256 -c` → **rc 0, 7,055/7,055 OK**; TASL-2 host-check report **`83636c03…`** (369 lines; reviewed
predecessor `0a1fa3a4…`) / review **`bfe9b231…`**; TASL-7 host-check report **`2b703226…`** / review
**`18e261cd…`**; seven-node R5 review **`9c604f1b…`** (363 lines / 36,103 B, conditions C1–C10); AR-row R4 review
`d4c3f9f0…` (255 / 25,428), R3 review `4c5f1848…` (292 / 26,580), R2 review `5fe423ac…` (328 / 30,312); superseded
addendum `fa7bb75d…` (22 / 1,770); `docs/r1/PLAN.md` at HEAD / `origin/main` `4aac5209` / `df58bcd5` —
`R1-TRACKG-AR-COND7` :1317, `R1-T1-HOST-H200` :1329, `R1-TRACKG-G3-EARLY` :1330, `R1-TRACKG-G0-GO` :1258,
`R1-TRACKG-LICENCES` :1269, `R1-TRACKG-PORT-DECISIONS` :1289, `R1-HARNESS-ISOLATION` :1290 all verified present
(`de3de54f:PLAN:1258` is `R1-TRACKG-G0-GO`); the author-signed `R1-TRACKG-AR-U2-TASL2` row is absent from both
committed PLANs, as the census/sidecar say; the seven earlier gate JSONs re-parse `verdict:"clear_finished"`,
`paper_a_live_waiting_for_card:false`, `evidence.gpu.paper_a_processes:[]`; the nine AR `run_record.json` files
re-parse as 8 executed + refused `s001`, every executed record `isolation.effective:true`, `waivers {}`,
`exceptions []`; `gate/gate_not_applicable.txt` and the exclusivity substitute are present; `run.log`
`AR_INFO parent_peak_vram_mb=6560.3`; the census tables were cell-counted (main table: header + 8 rows at 15
cells; run-level table: header + 8 rows at 5 cells) and rendered with `pandoc -f gfm` (rc 0, two tables).

**Verdict: NOT ACCEPTED — 0 BLOCKING, 3 MAJOR (record-only traceability), 7 MINOR, 1 traceability note.** The
measured content is unchanged and correct — all eight rows/values re-verified, rows 1–7 byte-identical to the
HEAD blob, the AR row matches its captures, captures **7,055/7,055 OK**, gate/isolation records true, and U4
still does not block G.1b/G.4 — and the R5 work did fix the dangling citations fragment, the readiness
sentence, the duplicate fix-review name, the authority-row citations, the intermediate U2 chain items and the
sidecar→census sha binding. But the **final post-R5 edits moved both objects and the recorded deltas were not
recomputed**: the U2 result grew from `ee21f6d9…` 73/5,484 to `86bdd429…` 76/5,841 (+3/+357) and the census from
`ef001f89…` 139/14,565 to `26a30673…` 140/15,045 (+1/+480), while the census/sidecar/U2-result still quote the
pre-final deltas (`+16/+1,591` and `+280`; `+16/+1,931` and `+3/+581`). The census also still cites the
superseded `ee21f6d9…` as the U2 result's "current sha". In addition the pair remains **uncommitted** (the final
census sha is not commit-reachable; sidecar and all AR evidence are untracked), and the newly added "R5-carried
conditions C4–C10 dispositions" list **does not correspond to R5's actual C4–C10** and presents several open
conditions as applied. Because the binding sidecar is the acceptance record and its chain figures are
arithmetically inconsistent with the object it binds, this pair cannot yet be taken as the final U4
record/binding. No measured value is wrong and nothing needs re-running; the defects are documentary.

---

## 1. Confirmations that do hold (measured content unchanged; captures; binding design; U4 readiness)

- **Seven earlier rows unchanged.** Main-table rows 1–7 and run-level rows 1–7 are **byte-identical** to the
  HEAD blob `146b1114…` (per-node row comparison; only the AR row was added). Their gate JSONs re-parse
  `clear_finished` / key false / `paper_a_processes:[]`. Their measured values are therefore unchanged and
  remain covered by seven-node R5.
- **AR row values unchanged and independently re-verified from the smoke/captures.** B1 `218.951 s` /
  `1.293937 (val_bpb)`; B2 `218.443 s` / `1.293937` (exact); sealed `n/a`; timeout `656.853 s` (= 3 × 218.951);
  upper bound `12,436 MiB`; `GPU-4d623e76…` (TASL-2 4090), cpus 0-7; committed pin `147f0d35…` (20 entries);
  manifest `ab7186d2…`; record cell `U2_ISO_AUTORESEARCH_RESULT_20261121.md` + captures dir + `7,055/7,055 OK` +
  `SHA256SUMS 32f5009a…`. The run-level AR row matches the captures: `3,204,520 kB` max RSS; deployed pin
  `ca049086…` (21, path-dependent); `gate_not_applicable.txt`; disk `388,531,040,256 → 388,344,332,288 B`. The
  AR notes match: `1,791.0 s`, `3.176×` (1,791.0/564 = 3.176), `1,980.1 MB`, `3,720.4 MB`, `6,560.3 MB`, cgroup
  peak `5.17 GiB` with OOM 0/swap 0, sampler upper bound `12,436 MiB`, CPU memfd/no CUDA IPC, pins 20/21.
- **Captures unchanged and complete.** `SHA256SUMS` **`32f5009a…`**, 7,055 entries, 7,056 regular files, 17
  symlinks, 2,128 dirs; `shasum -a 256 -c` → **rc 0, 7,055/7,055 OK**. No capture edited; no re-run, no second
  U2, ENGINEERING_ONLY raw-cost row.
- **Citations/authority rows now correct.** Host-check report/review shas all match the files (`83636c03…` /
  `bfe9b231…`, `2b703226…` / `18e261cd…`); AR smoke `8814eecc…`, captures `32f5009a…`, U2 review `9de24ec5…`;
  the result-review count is fixed ("two result reviews cover the six earlier torch nodes"); `R1-TRACKG-AR-COND7`
  (PLAN:1317), `R1-T1-HOST-H200` (:1329) and `R1-TRACKG-G3-EARLY` (:1330) are cited and verified present;
  the TASL-2 report is recorded as successor of `0a1fa3a4…`.
- **C3 labels present.** `:8`/`:43` "no U2 retry" qualified by the `:9–10` external-contention disclosure;
  `:65` labels `3.225×` a **cross-host composite** (bpb/VRAM not normalised); `:97` labels `0.2345 s/request` a
  **wall-clock surrogate**; the AR smoke is a single `port_smoke_gpu`; 8 executed + refused `s001`.
- **Sidecar→census sha binding is exact (design sound).** The sidecar's `26a30673…` rehashes the current census
  exactly; the census defers to the sidecar as the binding record (the only sound way to avoid a document
  containing its own hash); the sidecar was written after the final census edit (04:36:34Z vs 04:36:27Z).
- **U4 does not block G.1b/G.4 — confirmed.** `R1-TRACKG-G3-EARLY` (:1330) sets the six earlier nodes for
  G.1b/G.4 now and lets HousePrice/autoresearch join once their U2 passes; the census readiness text says the
  census does not block G.1b/G.4 and is not evidence; that is correct, and U4's acceptance is not a
  G.1b/G.4 gate. (This record defect does not change that status.)
- **No BLOCKING, no fabricated/overclaimed measured value, no re-run.** The defects below are documentary.

## 2. MAJOR-1 — U2 chain/deltas and the "current" sha are stale (R5 C1 not closed)

R5 C1 required: reviewed `ca3bcadd…` (57/3,893, not preserved) → `8430854c…` (67/5,181) → `c03f0cbd…`
(67/5,204, +23 B parent-peak) → current (73/5,484 at R5 time) with the correct reviewed→current total
(**+16/+1,591 B**), the intermediate wording, the sibling's 74 lines / 6,374 B, the open U2-review C3/C4
residuals, and correction of the U2 result's own revision note.

The chain items are now present, but the numbers no longer describe the object the sidecar binds:

- **Census `:126` still cites a superseded "current" sha.** It says "AR U2 result current sha `ee21f6d9…`".
  `ee21f6d9…` is the R5-era object **73 lines / 5,484 B** (R5 review `:26`); the final, sidecar-bound object is
  **`86bdd429…`, 76 lines / 5,841 B** (sidecar `:7`; measured). The same sentence then says "current size/sha
  recorded in the U4 acceptance sidecar", so it simultaneously claims two different current objects.
- **Sidecar `:8` is arithmetically inconsistent with itself.** It reads "→ current 76/5,841 B (+16 lines/+1,591 B
  from reviewed, +280 B from c03f)". With reviewed 57/3,893 and `c03f0cbd` 67/5,204:
  +16 lines → 73, not 76; +1,591 B → 5,484, not 5,841; +280 B → 5,484, not 5,841. The recorded deltas are
  exactly the reviewed→`ee21f6d9` and `c03f`→`ee21f6d9` steps. For the bound final object the true figures are
  **reviewed→final = +19 lines / +1,948 B** (76−57; 5,841−3,893) and **`c03f`→final = +9 lines / +637 B**
  (76−67; 5,841−5,204); the intermediate `8430854c→c03f` step is +23 B (67 lines), and `8430854c→final` is
  +9 lines / +660 B.
- **The U2 result's own revision note repeats the stale delta.** `:71–73` says "Current sha/size are recorded in
  the U4 acceptance sidecar; reviewed→current = +16 lines/+1,591 B, and `c03f0cbd…`→current +280 B". The
  sidecar it points to binds 76/5,841, whose true deltas are +19/+1,948 and +9/+637. R5 C1's requirement to
  correct this note is therefore not met (it was rewritten, but the rewrite itself changed the object's size
  and the deltas were not recomputed).
- No measured value is affected: the smoke/captures still give B1 218.951 s / bpb 1.293937, B2 218.443 s exact.
- Residual (carried as m5 below): where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved
  is still not recorded; the U2 result only lists "author-row record location" as an open residual.

**Evidence of cause.** The U2 result's mtime is 04:36:27Z (same second as the census); R5 measured the U2 result
at 04:17:39Z as 73/5,484. The final edit added exactly +3 lines / +357 B (5,841−5,484 = 357), consistent with the revised
revision-note text and arithmetic (`ee21f6d9→86bdd429`), and the deltas were copied forward from the pre-edit
object.

## 3. MAJOR-2 — Census binding-chain deltas are stale, and the pair is still uncommitted (R5 C2/C5 not closed)

R5 C2 required: after the final census edit, recompute the R3→current delta and rewrite the sidecar **last** so
it binds the then-final census sha and states the **correct** delta (at R5 time: `79ad29ca…` 123/12,634 →
`ef001f89…` 139/14,565 = **+16/+1,931 B**) and record R5's carried conditions. R5 C5 required committing the
final census with the sidecar and cited AR evidence and re-running `shasum -a 256 -c` (preserve the revision).

- **The delta is wrong for the bound object.** Census `:132–133` and sidecar `:10` state "R3 object
  `79ad29ca…` (123 lines/12,634 B) → final revision … R3→final delta is +16 lines/+1,931 B and R4→final
  +3 lines/+581 B". The final revision is **140 lines / 15,045 B** (sidecar `:6`; measured), so the true
  R3→final delta is **+17 lines / +2,411 B** (140−123; 15,045−12,634) and, with the R4 object `2dbf2c16…`
  at 136 lines / 13,984 B (R5 review `:21`), R4→final is **+4 lines / +1,061 B**. The quoted `+16/+1,931` and
  `+3/+581` are exactly the R3→R5-object and R4→R5-object steps (`ef001f89…` = 139/14,565). The same paragraph
  is self-contradictory: it says the "final revision (exact lines/bytes recorded in the sidecar)" — which the
  sidecar records as 140/15,045 — and then gives a delta that reaches only 139/14,565.
- The sidecar was written **last** (04:36:34Z, 7 s after the census/U2 edits) yet still carries the pre-final
  delta; the final edit added exactly +1 line / +480 B (15,045−14,565 = 480), consistent with the sidecar-pointer
  sentence, and the delta was not recomputed. "As measured at integration" does not repair a figure attached to
  "R3→this".
- **Still uncommitted / not preserved.** HEAD is `ebe03cd5` (last commit 01:11:17Z), unchanged since before R5.
  The census is tracked-modified; the sidecar, U2 result, unit sibling, smoke report and the 7,056-file capture
  bundle are all untracked (`??`); the final census sha `26a30673…` is not reachable from any ref/commit (a
  `git rev-list --all --objects` scan shows only the HEAD blob `6d1ac47f…` for the census path). There is no
  commit after R5 and no preserved snapshot of the final pair. R5 C5 (commit the final census with sidecar and
  cited AR evidence; re-run `shasum -c`; verify the sidecar sha still matches) and seven-node R5 C9/C10
  (preserve the accepted revision; commit the hashed AR evidence or state the SHA256SUMS caveat) are all still
  outstanding. The "uncommitted traceability" MAJOR from R5 recurs: if this in-place object is edited again, it
  is lost like its predecessors.
- **Note.** The seven-node R5 review's rules allow C2–C10 to be carried as recorded conditions, but the
  commit/preservation part is not a wording correction and was expressly one of R5's two MAJORs.

## 4. MAJOR-3 — The "R5-carried conditions C4–C10 dispositions" list is mis-mapped/false

R5 (seven-node) conditions C4–C10 are, verbatim from `TRACKG_U4_CENSUS_REVIEW_R5_20261120.md` `:308–:323`
(restated in AR-row R4 review `:184–186` and AR-row R5 review `:184–191`): **C4** remove the duplicated
`HARNESS_ISOLATION_FIX_REVIEW_20261119.md` occurrence; **C5** complete the licence/availability column per U1 §7;
**C6** give shas and complete the citations (kit-update reviewed/current sha + C-K1–C-K5, per-node unit
reviews, the three result reviews, U4 basis docs, U1 audit, G3-EARLY attribution, AR code-review "0 BLOCKING" +
C1–C6); **C7** insert the verbatim mandated imdb sentence and drop the self-referential clause; **C8**
reconcile the "whole-smoke CPU/RAM aggregates labelled" wording; **C9** bind/preserve the accepted revision;
**C10** commit the hashed AR evidence (or state the SHA256SUMS caveat).

The census `:134–137` instead records: "C4 licence/availability row added …; C5 host-check caveat added …;
C6 record-cell captures sha added; C7 no-retry/cross-host/surrogate labels added; C8 authority rows added;
C9 revision/sidecar chain added; C10 open residual = U2 result reviewed bytes not preserved and U2-review C3/C4
text residuals". Those items do not correspond to the actual conditions (they appear to be a mixed list of this
revision's own edits and AR-row/U2-review residuals), and several are claimed from content that is not there:

- **C4 (actual):** the duplicate fix-review name *is* removed (one occurrence at `:86`), but the list does not
  record that; it instead claims the licence/availability row was completed.
- **C5 (actual licence):** the AR licence cell `:23` still reads "README-MIT / climbmix MIT-claimed, no LICENSE
  file; data available; option A CPU transport" — "data 963 M" appears **only inside the disposition line
  itself** (grep: `963` occurs nowhere else), the other seven cells are unchanged generic citations, and
  availability is still not given to U1 §7 level (no public/HTTP-200, HF revision, data-present/963 M in the
  cells). The claim "data 963 M available" for the *row* is therefore not true.
- **C5 (claimed host caveat):** the actual host caveat `:114–115` correctly says CUDA IPC is untested, option A
  uses the CPU memfd path only and no `cuda_share`/`cuda_open` node is covered, but it does **not** say "AR
  option-A gate only", and "§5 item 5/§5.5 open" appears **only inside the disposition sentence** (grep), not in
  the caveat. The sidecar `:11` ("both option-A host gates, not §3 item-7 CUDA-IPC passes") is accurate.
- **C6 (actual citations):** still names-only/incomplete: kit-update report cited without sha (current
  `fe232e2b…` vs reviewed `3c3ae74a…`, review `d8c68f9f…`, C-K1–C-K5), the three earlier result-review shas are
  not given (`965dc993…`, `d4cdd9bb…`, `b2c463a7…`), no per-node unit-review shas, no U4
  basis docs, no U1 audit, no AR code-review "0 BLOCKING" + C1–C6, and G3-EARLY is not attributed to
  `94db94bb`/`origin/main df58bcd5` (it is listed as `:1330` only). The claimed "record-cell captures sha added"
  is true but is not C6.
- **C7 (actual imdb):** the mandate is still a paraphrase with the self-referential clause "the census/paper
  appendix must carry this disclosure" (`:57–58`); no verbatim sentence inserted. The claimed "no-retry/cross-
  host/surrogate labels" are a different (AR-row R5 C3) item.
- **C8 (actual CPU/RAM):** `:46` still says "whole-smoke CPU/RAM aggregates labelled", which overstates the
  content (only whole-smoke max RSS and a VRAM upper bound are carried; CPU time is only in the captures). The
  claimed "authority rows added" is a different item (and is true).
- **C9/C10 (actual preserve/commit):** not done (see MAJOR-2). The disposition substitutes an unrelated "open
  residual" for C10 and silently drops the commit-of-AR-evidence condition.
- The sidecar `:10` builds on this list: "this revision applies R4/R5 C1–C5: full U2/census delta chain …
  R5 C4–C10 dispositions …" — an overclaim (C1 partly, C2/C5 not; the dispositions are mis-mapped).

This is a record-only defect of exactly the traceability class R4/R5 rejected; no measured value changes.

## 5. Minor findings

| # | severity | where | finding |
|---|---|---|---|
| m1 | MINOR | sidecar `:10` | "AR R5 NOT ACCEPTED (3 MAJOR traceability)" — R5's verdict is **2 MAJOR** (R5 review `:48`); **R4** had 3 MAJOR (R5 review `:20`). The same line also overclaims "this revision applies R4/R5 C1–C5". |
| m2 | MINOR | census `:123`, `:96–97` | R5 C3 residue: "successor of **pre-fix** `0a1fa3a4…`" should be "amended successor of **reviewed** `0a1fa3a4…`" (the reviewed object is not a pre-fix report); the Blocked section still says "the earlier Ada attempt"/"vs Ada 67.901 s" without naming the 17 Nov Ada un-isolated U2 (named at `:65`), and its `3.225×` is not labelled a composite. |
| m3 | MINOR | census `:23` | R5 C4 residue: the record cell carries the captures sha and `7,055/7,055 OK` but not the smoke sha `8814eecc…` beside the record; licence/availability not to U1 §7 (963 M/HF revision/public availability) and methodology "option A CPU transport" remains in a licence cell. |
| m4 | MINOR | census `:114–115` | R5 C4 residue: host caveat lacks the explicit "AR option-A gate only" wording; `HARNESS_ISOLATION` §5 item 5/§5.5 "open" is not stated in the caveat block (only inside the disposition sentence). |
| m5 | MINOR | census `:75–80`; U2 result `:75–76` | R5 C1 residual: where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved is still not recorded (U2 review m3/C3); it is listed only as an open residual. |
| m6 | MINOR | census `:107` | "All eight rows are complete in the census sense" remains a weak qualifier; R4 C5(v)/R5 m8 asked for the U2 review's conditional C1–C5 / ENGINEERING_ONLY raw-cost status in the completion sentence. |
| m7 | MINOR | sidecar `:10` | The acceptance chain names accepted objects (`4e050ad2…`, `76bf88db…`, `79ad29ca…`) but not the accepting review shas (seven-node R5 `9c604f1b…`, AR R2 `5fe423ac…`, R3 `4c5f1848…`) nor the R4/R5 rejection shas (`d4c3f9f0…`, `8737edf4…`), so the chain is not self-verifiable from the binding record (R5 m7). |
| t1 | traceability note (not a finding against a value) | — | The final pair is not preserved: census `26a30673…` is tracked-modified and not commit-reachable; the sidecar, U2 result, unit sibling, smoke report and captures are untracked; earlier objects `2dbf2c16…`/`ef001f89…`/`79ad29ca…`/`4e050ad2…`/`ee21f6d9…`/`ca3bcadd…`/`8430854c…`/`c03f0cbd…` are not preserved either. The sidecar must be rewritten **after** the final edit and must state the delta recomputed at the final sha (R5 C2/C5). |

**No BLOCKING was found, and no fabricated, overclaimed or altered measured value was found.** The eight rows are
unchanged and correct, the captures verify 7,055/7,055, all cited shas match the delivered files, and the census
remains an ENGINEERING_ONLY U2 raw-cost record that does not block G.1b/G.4. However the three MAJOR record-only
traceability defects above mean the pair cannot yet be accepted as the final U4 record/binding, so "no new
MAJOR/BLOCKING" **cannot** be confirmed in the record sense.

## 6. Conditions (documentation/record only — no re-run, no measurement/record edit)

- **C1 (before commit; MAJOR-1).** Recompute the U2 chain at the final object `86bdd429…` (76/5,841): reviewed
  `ca3bcadd…` (57/3,893) → `8430854c…` (67/5,181; +10 lines/+1,288 B) → `c03f0cbd…` (67/5,204; +23 B
  parent-peak) → current `86bdd429…` (76/5,841; +9 lines/+637 B from `c03f` and **+19 lines/+1,948 B** from
  reviewed). Replace census `:126`'s superseded "current sha `ee21f6d9…`" (or make the deferral to the sidecar
  unambiguous), correct sidecar `:8`, and correct the U2 result `:71–73` note with the recomputed totals; add the
  preservation location of the author-signed row (or state it is not preserved and where delegated).
- **C2 (before commit; MAJOR-2).** Recompute after the final census edit: R3 `79ad29ca…` 123/12,634 → final
  `26a30673…` 140/15,045 = **+17 lines/+2,411 B**; R4 `2dbf2c16…` 136/13,984 → final = **+4 lines/+1,061 B**.
  Write the sidecar last so it binds the then-final sha and state these figures; remove "as measured at
  integration". Any further content edit invalidates the sidecar binding and needs a fresh binding (and a fresh
  review if more than these delta/sha lines change).
- **C3 (before commit; MAJOR-2).** Commit the final census **with** the sidecar and the cited AR evidence (U2
  result, unit sibling, host reports/reviews, smoke + captures) and preserve the accepted revision; after the
  commit re-run `shasum -a 256 -c SHA256SUMS` and verify the sidecar sha still matches. Because the census bytes
  will change for C1/C2, the binding sha must be re-recorded; commit the final, re-reviewed bytes, not this
  revision.
- **C4 (MAJOR-3).** Replace the "R5-carried conditions C4–C10 dispositions" list with the actual R5 C4–C10 and
  an honest open/closed status, and either apply or carry: C5 licence/availability per U1 §7 (963 M/HF
  revision/public availability, per-node code/asset licence) or state it is carried open; C6 citations/shas
  (kit-update reviewed vs current sha + C-K1–C-K5; three result reviews; per-node unit reviews; U4 basis docs;
  U1 audit; AR code review "0 BLOCKING" + C1–C6; G3-EARLY attributed to `94db94bb`/`origin/main df58bcd5`);
  C7 verbatim imdb sentence, drop the self-referential clause; C8 CPU/RAM wording; C9 preserve; C10 commit AR
  evidence / state the SHA256SUMS caveat. Correct the sidecar `:10` overclaim and the "3 MAJOR" count.
- **C5 (MINORs).** Apply m1–m7: fix "pre-fix"; name the 17 Nov Ada un-isolated U2 in the Blocked section and
  label its `3.225×` composite; put smoke sha `8814eecc…` beside the record; complete the licence/availability
  cell; add "AR option-A gate only" and §5 item 5/§5.5 open to the host caveat; record the author-row
  preservation location; qualify the completion sentence; add accepting-review shas to the sidecar chain.
- **C6.** Because the record must change to fix C1–C4, one more final round (or a documented delta-only
  spot-check under the R4/R5 rules) is required; this review's binding is to the objects above and is void for
  any edited revision. Nothing in this review changes a measured number, pin, manifest, gate capture, isolation
  record or U2 status.

## 7. Acceptance binding and read-only attestation

This review binds to the pair: census
`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`26a306732d36b024fe3eb143579138b4357dfe322d10ffc49c4ad0dfd8e1fc01`**, 140 lines / 15,045 bytes, mtime
2026-11-21T04:36:27Z, tracked-modified at HEAD `ebe03cd5` (HEAD blob `146b1114…`); and sidecar
`TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md`, SHA-256
**`4880b3a039f1ff22927c2df5162070f41e7da274289b8c9fa6412b0e9e3f8c05`**, 12 lines / 2,618 bytes, mtime
2026-11-21T04:36:34Z, untracked. The verdict is **NOT ACCEPTED**: the measured content, captures, rows and
citations are correct and the pairing design is right, but the binding pair's deltas are stale relative to the
final objects it binds (both the U2 chain and the census chain), the census still cites a superseded U2 sha as
current, the pair remains uncommitted/unpreserved, and the R5-carried C4–C10 disposition list is mis-mapped and
presents open conditions as applied. The next revision must recompute the deltas at the final shas, correct the
U2 result's revision note, record the actual R5 C4–C10 statuses, write the sidecar last, and **commit** the final
census with the sidecar and the cited AR evidence so the accepted revision is preserved.

**Written:** only this review file (untracked). **Read-only:** all cited files, captures and records;
`shasum -a 256`; `shasum -a 256 -c` (captures 7,055/7,055 OK, rc 0); JSON re-parses of the seven earlier gate
JSONs and all nine AR run records; `pandoc -f gfm` render check (rc 0, two tables); cell counts;
`git rev-parse/status/log/show/rev-list/cat-file/for-each-ref/fsck`; `wc`, `stat`, `grep`, `diff`, `sed`, `read`.
**Not done:** no run, smoke, U2/GPU/T1/census job, probe, SSH/live-host inspection, edit outside this review,
commit, push, deletion/move, HTCondor/deepthought action, or secret/credential read. No other review's object was
modified. This is the AR-row review round 6; it is distinct from the seven-node census review
`TRACKG_U4_CENSUS_REVIEW_R5_20261120.md`.
