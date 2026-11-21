# Independent review — Track G U4 census update adding the `autoresearch_fixedtokens` TASL-2 row (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2 host check, the AR unit/result, the AR smoke, the U4 census or any
earlier U4 review. **Read-only:** the only file written is this review (untracked, no commit/push). No run,
smoke, U2/GPU/T1/census job, probe, edit of any other file, deletion/move, HTCondor or deepthought action.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`8c0c0173ae47980985a35ec6992230532c5714461582374153c62c8d8168c54c`**, **101 lines / 10,251 bytes**, mtime
**2026-11-21T03:47:56Z**, **tracked and modified** in the worktree at HEAD **`ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`**
(`origin/ops-tasl-20261116` = same; `origin/main` = `4aac5209`). The HEAD blob is `6d1ac47f…` = SHA-256
`146b111410122108c7efa25246b61db62060adcaa3ea14fb2111ec2e13d692d7`, the R5-accepted/C1-repaired census
committed at `76f1d7ba`, so the prior accepted revision is preserved in git and the delta is auditable. The
delta is **+9/−17 lines**: the 8th passed row, the rewritten `Blocked / not passed` bullet and one readiness
clause. The seven earlier rows, the funnel appendix, the run-level facts and the acceptance citations are
**unchanged** (git diff).

**Inputs / authority read (all local, read-only).** The new AR U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` SHA-256 **`4689c673f909fbee58ed37289cd4807d532ac4cea4beef9a2a7890bbf6ac83d8`**,
66 lines / 5,085 B, untracked, mtime 03:47:48Z (amended after its review); its review
`U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` SHA-256 **`9de24ec5ebd38825b4f352deeeb7df6a9b5f2d0d1890258119bc2368b4c16aaa`**
(verdict **ACCEPTED — 0 BLOCKING, 1 MAJOR report-only, 12 MINOR, conditional on C1–C5**; the reviewed object is
`ca3bcadd…`, 57 lines / 3,893 B, **not preserved anywhere in the worktree**); the smoke report
`TASL2_AR_COND7A_RESULT_20261121.md` SHA-256 **`8814eecc1fb0f9ded4920adc15aa276a05c08e5a181a0a1ed4c5d564f088d0ad`**
(288 lines / 22,667 B) and captures `TASL2_AR_COND7A_RESULT_20261121_captures/` (`SHA256SUMS` SHA-256
**`32f5009a347264bb1d820c420dedeaf0d2dd5fe8822516597f1bba53a3ca0aeb`**, 7,055 entries, 7,056 files,
`shasum -a 256 -c` **rc 0, 7,055/7,055 OK**); TASL-2 host check `TASL2_ISOLATION_HOST_CHECK_20261121.md`
**`0a1fa3a4…`** and review `TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` **`bfe9b231…`** (ACCEPTED, C1–C4);
U2 result review-vs-current delta; the 17 Nov Ada un-isolated baseline `TRACKG_U2_AR_RESULT_20261117.md`
**`a6ddfbd0…`** (B1 67.901 s, `val_bpb` 1.291068, Ada/L40S `GPU-9be33fd1…`); the 20 Nov STOP record
`ar_cond7a_smoke_20261120T223548Z/` (`U2_ISO_AR_COND7A_RESULT_20261120.md` `bcb74efc…`, `SHA256SUMS`
`231d388e…`) and the 21 Nov retry STOP `ar_cond7a_retry_20261120T232847Z/R1_TRACKG_AR_COND7A_RETRY_RESULT_20261121.md`
**`34bd3532…`**; the committed addendum `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` **`fa7bb75d…`**; the U2 unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md` **`b83d9159…`** (74 lines) and its
review `ef42276d…`; the R5 review `TRACKG_U4_CENSUS_REVIEW_R5_20261120.md` **`9c604f1b…`** (363 lines);
`docs/r1/PLAN.md` **`7e0e160a…`** (`R1-TRACKG-AR-COND7` `:1317`, `R1-T1-HOST-H200` `:1329`,
`R1-TRACKG-G3-EARLY` `:1330`); `U1_LICENCE_AVAILABILITY_20261117.md` §2/§7; `TRACKG_CENSUS_20261117.md`.
The AR captures were parsed directly (9 `run_record.json` = 8 executed + refused `s001`; `verify_full.json`
`ok:true`, `issues:[]`, `ipc_hits:[]`, `committed_pin 147f0d35…`, `deployed_pin ca049086…`; sampler max
12,436 MiB; `time_v.txt`; `disk_before/after.txt`; `gate/gate_not_applicable.txt`; `prep/pins_committed.txt`;
`data_manifest.txt`); the census was cell-counted and `pandoc -f gfm` render-checked. Nothing was re-run and
no live host was contacted.

**Verdict: NOT ACCEPTED — 0 BLOCKING, 2 MAJOR (both report-only), 11 MINOR, 1 dependency-record finding;
conditions C1–C8 below (documentation/record only; no re-run, no measured-value change).** The 15 cells of the
new row are **all correct** and independently reproduced from the delivered records; there is **no fabricated
or overclaimed AR number**. The census is not acceptable because the update is only half-integrated: the
per-suite appendix still tells the reader that autoresearch is **"not in this census"** and that its smoke was
STOPPED with no measured slowdown, while the added row and the Blocked section say it passed on TASL-2; and the
run-level facts / gate / readiness / citation sections still describe the seven-row blocked state. These are
status-text defects, not measurement defects.

---

## 1. What the update does and the mechanical checks

- The main table gains the eighth row (line 21); the `Blocked / not passed` bullet (lines 78–84) is rewritten
  to "all eight nodes have now passed"; the readiness last clause (line 90) is replaced. Nothing else changes
  (`git diff`: 9 insertions, 17 deletions).
- **Table structure/render (R5 C1 remains closed):** main table header/delimiter/all 8 data rows = **15 cells**
  each; run-level table header/delimiter/7 rows = **5 cells** each; `pandoc -f gfm -t html` emits **two
  tables** (9 and 8 `<tr>`) and the main table has 15 `<th>`. No formatting regression.
- The four sections that still describe the pre-update state: the per-suite appendix autoresearch bullet
  (lines 59–61), the run-level facts table + "All seven rows" paragraph (lines 25–44), the readiness sentence
  (lines 89–90) and the acceptance citations (lines 93–101). Their unchanged state is the substance of the two
  MAJORs below.

## 2. The new row — all 15 cells verified (values correct)

*All values recomputed from `TASL2_AR_COND7A_RESULT_20261121_captures/`, cross-checked against the U2 result
and the smoke report; no value was taken from the census.*

| # | cell | census value | verified against | result |
|---|---|---|---|---|
| 1 | node | `autoresearch_fixedtokens` | record `node`/result title | ✅ |
| 2 | suite | `autoresearch` | U1 §2 suite | ✅ |
| 3 | kit tip | `7330338…` | `73303380197477…` in smoke §2.2; U2 result §Kit | ✅ |
| 4 | B1 elapsed | `218.951 s` | `s000_baseline/run_record.json` `elapsed_seconds_info_only: 218.951` | ✅ |
| 5 | B1 metric | `1.293937 (val_bpb)` | same record `outcome.value: 1.293937` | ✅ |
| 6 | B2 elapsed | `218.443 s` | `runs/runs_edits/B2/run_record.json` `218.443` | ✅ |
| 7 | B2 metric | `1.293937 (val_bpb)` | identical to B1 (B2 exact) | ✅ |
| 8 | sealed test | `n/a` | `sealed: null` in every record | ✅ |
| 9 | timeout = 3×B1 | `656.853 s` | 3 × 218.951 = 656.853 (same rule as the seven rows) | ✅ |
| 10 | whole-smoke upper bound | `12,436 MiB` | `sampler/sampler_max.json` `max_per_sample_sum_mib: 12436` (labelled upper bound) | ✅ |
| 11 | GPU/cpus | `GPU-4d623e76…` (TASL-2 4090), cpus 0-7 | records `limits.gpu_uuids` / `cpu_list [0..7]`; host §2.1 | ✅ |
| 12 | committed-file pin | `147f0d35…` | `prep/pins_committed.txt` 20 entries = `147f0d35d40d…` | ✅ |
| 13 | data manifest sha256 | `ab7186d2…` | `data_manifest.txt` = `ab7186d2…`, 13 files / 1,009,004,449 B / 963 M | ✅ |
| 14 | record | `U2_ISO_AUTORESEARCH_RESULT_20261121.md` | file exists; captures dir exists | ✅ cell exists, but see m6 (semantics) |
| 15 | licence/availability | `autoresearch MIT/climbmix MIT-claimed; option A CPU transport` | U1 §2/§7: code MIT *declared* (README; no LICENSE file), climbmix dataset MIT *declared on the HF card* (uploader assertion) | ✅-ish, see m7 |

No 17 Nov un-isolated number (67.901 s / 5,211.3 MB / 1.291068) is used as a TASL-2 row value. The row is a
genuine isolated option-A TASL-2 measurement: every executed record `isolation.effective:true`,
`waivers {}`, `exceptions []`, private `/dev/shm`, no CUDA-IPC usage; `verify_full.json` `ok:true`,
`issues:[]`, `ipc_hits:[]`; 8 executed + refused `s001`; `CHECKLIST_E_PASSED`; no synthetic marker; slowdown
measured. **No fabricated value was found anywhere in the AR row.**

## 3. Cross-checks against the AR result/review, the smoke and the previous census

- **Host difference disclosed — partly.** The row's GPU cell says "TASL-2 4090" and the Blocked bullet says
  "one host difference TASL-2/4090 vs the earlier Ada attempt". This is the U2 result's own wording. It does
  **not** identify the comparison baseline as the **17 Nov Ada, un-isolated** U2 (`67.901 s`, L40S
  `GPU-9be33fd1…`); "the earlier Ada attempt" can equally be read as the 20 Nov stopped smoke (which produced
  no B1 and no slowdown). See m3.
- **3.225× cross-host slowdown — arithmetic correct.** 218.951 / 67.901 = 3.2246 → **3.225**; the 0.2345
  s/request is (218.951−67.901)/644 = 0.23455. The ratio is a **cross-host composite** (option-A CPU memfd
  transport **plus** 4090/24,564 MiB TASL-2 vs L40S/48 GiB Ada; `val_bpb` +0.002869 and VRAM not normalised),
  and 0.2345 s is a **wall-clock surrogate**. The census calls it "cross-host option-A slowdown", attributing
  the whole ratio to option A; the U2 review m11 required the "option A + host change" label. See m3.
- **All eight nodes now pass — the row and the Blocked bullet are correct, but the appendix contradicts them.**
  The seven earlier rows are unchanged (byte-identical to HEAD), and the AR row is a real U2 pass; however the
  appendix (lines 59–61) still says autoresearch is **"not in this census"**, its **"one isolated Ada smoke was
  attempted and STOPPED"**, **"slowdown not measured"** and it **"joins after a fresh clean isolated smoke + U2
  review"**. That is MAJOR-1.
- **No blocked node left / 20 Nov + retry STOP preserved as historical — correct in the Blocked section but
  no longer cited.** The committed evidence survives (`ar_cond7a_smoke_20261120T223548Z/`, report
  `bcb74efc…`, `SHA256SUMS` `231d388e…`; retry `R1_TRACKG_AR_COND7A_RETRY_RESULT_20261121.md` `34bd3532…`),
  but the rewritten bullet dropped those record paths and shas and only says "remain preserved". See m4.
- **Readiness / G3-EARLY — stale and over-stated.** `PLAN.md:1330` says AR joins **as soon as its U2 passes**
  (with the `AR-COND7` smoke precondition); the U2 now passed, so AR joins now. The census still says
  "autoresearch joins when its option-A smoke + U2 pass" and lists only the six + HousePrice as set; its final
  clause "all eight rows are now complete (AR on TASL-2 per the author row)" is an unconditional completeness
  claim while (a) the author-signed `R1-TRACKG-AR-U2-TASL2` row is **not in committed `docs/r1/PLAN.md`**
  (only reports/captures mention it) and (b) the U2 result review is **conditional on C1–C5** (see §5). See
  m1/m2.
- **No evidence / no noise floor / no D21–D28 / no T1 label — correct.** Census line 6 and line 90 carry the
  explicit statements; the AR row is an ENGINEERING_ONLY U2 raw-cost row, and T1 labels remain H200
  (`PLAN:1329`, per the U2 result's note). The census does not cite `R1-T1-HOST-H200` — see m5.
- **Census does not block G.1b/G.4 — correct** (line 90), and the census is explicitly "not evidence".
- **TASL-2 host check status.** The host check is ACCEPTED **for the AR option-A gate only**, with conditions
  C1–C4, and §3 item 7 CUDA IPC remains **UNTESTED** (host-check review `bfe9b231…`). The census's "TASL-2
  host checks PASS/accepted" inherits the host report's report-only M1 overclaim unless it adds "for option A;
  item 7 untested". The bullet's "no CUDA IPC" covers the run, not the host gate. See m2.

## 4. Findings

### MAJOR-1 (report-only) — the per-suite appendix still says autoresearch is "not in this census" and its smoke was STOPPED

Lines 59–61 (unchanged by the update) read verbatim:

> "**autoresearch (1 node):** not in this census; condition-7 option-A code unit accepted, but the one
> isolated Ada smoke was attempted and STOPPED (external co-tenant CUDA OOM; slowdown not measured; no
> retry). It joins after a fresh clean isolated smoke + U2 review."

The same document now has the AR row in `Passed rows` (line 21) and says "All eight nodes have now passed
isolated U2" and "No node remains blocked" (lines 78–85). This is the **same class of defect as the R4 MAJOR
M1** that R5 closed by rewriting this bullet (R5 review `9c604f1b…` §1.2/§1.3): the census again contains two
incompatible statements about whether autoresearch is in the census and has a valid measurement. A reader
following the appendix would conclude the row is absent and still blocked; a reader following the table would
conclude it passed. The fix is a one-paragraph rewrite, no re-run.

### MAJOR-2 (report-only) — the new row is not integrated into the census's run-level facts, gate envelope or counts

The update added the row only to the main table. The census still says:

- `Run-level facts` (lines 23–33) is a **seven-row** table; the AR row has no whole-smoke max RSS
  (captures `time_v.txt`: **3,204,520 kB**), no deployed run-record pin (records: **`ca049086…`, 21 entries**
  — the census's own note at lines 35–36 says the deployed pin is the run-record value and "not
  interchangeable", yet AR's is nowhere in the census), no gate capture, no disk before/after
  (captures: `/dev/nvme0n1p2` available **388,531,040,256 → 388,344,332,288 B**), and no co-tenancy-monitor
  result (879 ticks, 0 foreign compute apps).
- "All seven rows: … 8 executed + refused `s001` … **Paper-A three-check gate clear**" (lines 39–41) and
  "**Each row's gate JSON is `clear_finished`**" (lines 36–37) do **not** cover the eighth row: AR has **no
  Paper A gate** — `gate/gate_not_applicable.txt` = `paper_a_gate=NOT_APPLICABLE_ON_TASL2`, with substitute
  controls (0 compute apps at launch, exclusive `flock`, 1 s compute-app sampler, co-tenant abort monitor), and
  the U2 result's deviations also include the **20,000 MiB qualifier floor instead of 40 GiB** and the
  `ar-cond7a` env. The census's Blocked bullet says only "one host difference"; a paper/appendix reader can
  no longer tell that the TASL-2 row was measured **without** the Paper-A gate that the seven earlier rows
  used. "All eight rows are now complete" (line 90) is therefore not supported by the census's own facts.
  The fix is documentation: add the AR run-level row/label and the gate/floor deviation (or a sentence that
  the TASL-2 row substitutes exclusivity controls for the Paper-A gate, citing `gate/gate_not_applicable.txt`).
  Optionally carry the U2 review C2 figures the census does not record (whole-smoke wall **1,791.0 s**,
  **3.176×** whole-smoke ratio, worker peak **1,980.1 MB**, cgroup peak **5.17 GiB**).

### MINOR

- **m1 — readiness sentence / "complete" overclaim (lines 89–90).** "autoresearch joins when its option-A
  smoke + U2 pass" is stale (they passed); G3-EARLY says join on U2 pass, so say AR joins now (subject to
  `R1-TRACKG-AR-U2-TASL2` landing on main and the U2 acceptance conditions). The clause "all eight rows are
  now complete (AR on TASL-2 per the author row)" should be qualified: the row is a U4 raw-cost row, not T1
  evidence; the author row is not on committed main; the U2 result is conditional C1–C5.
- **m2 — "accepted" is unqualified and the TASL-2 host-gate caveat is missing (lines 79–82).** The U2 result
  review (`9de24ec5…`) is ACCEPTED **conditional on C1–C5** (report-only); the census cites no review sha and
  no accepted-object sha. The host check is accepted only for the AR option-A gate with item 7 CUDA IPC
  UNTESTED (`bfe9b231…`); the census's "TASL-2 host checks PASS/accepted" should carry that caveat (the row
  already says "no CUDA IPC", but that is about the run, not the untested host condition).
- **m3 — baseline/label wording (lines 80–82).** "vs the earlier Ada attempt" should be "vs the 17 Nov Ada
  **un-isolated** U2 (`B1 67.901 s`, `val_bpb 1.291068`, L40S)"; state that **3.225× is a cross-host composite
  (option A + 4090 vs L40S; bpb/VRAM not normalised)** and that **0.2345 s is a wall-clock surrogate**; and
  the "one host difference" understates the TASL-2 adaptations (env Py3.12.15 `ar-cond7a` vs 3.12.16
  `envs/torch312`, data root, 20,000 MiB floor, no Paper-A gate) — cross-reference the U2 result's deviations.
- **m4 — historical STOP citations dropped (lines 82–83).** The update removed the 20 Nov record path and
  shas (`ar_cond7a_smoke_20261120T223548Z/`, `U2_ISO_AR_COND7A_RESULT_20261120.md` `bcb74efc…`,
  `SHA256SUMS` `231d388e…`) and does not cite the retry result (`R1_TRACKG_AR_COND7A_RETRY_RESULT_20261121.md`
  `34bd3532…`). "Remain preserved as external co-tenancy evidence" is unverifiable from the census as written;
  restore the record cites as historical/superseded evidence.
- **m5 — AR acceptance/authority citations absent (lines 93–101).** The `Authority and acceptance citations`
  section still lists only the pre-AR inputs. Add: `R1-TRACKG-AR-U2-TASL2` (author-signed; not in committed
  PLAN — record the row/delegation provenance), `R1-TRACKG-AR-COND7` (`PLAN:1317`), the U2 result review
  `9de24ec5…`, the host-check report `0a1fa3a4…` / review `bfe9b231…`, the U2 result sha `4689c673…`, the
  smoke report `8814eecc…` / captures `32f5009a…`, and `R1-T1-HOST-H200` (`PLAN:1329`, T1 labels H200).
  The R5 C6 residuals also remain: "six isolated U2 result reviews" is still wrong (there are three reviews
  covering the earlier six nodes, plus the AR review), and `R1-TRACKG-G3-EARLY (:1330)` is still attributed
  to `de3de54f` where that line does not exist (it is at `94db94bb`/`origin/main`).
- **m6 — record-cell semantics and row formatting (line 21).** Every other row's `record` cell is a **record
  directory**; the AR row cites the U2 *result report* only and no record sha. Cite
  `TASL2_AR_COND7A_RESULT_20261121_captures/` (SHA256SUMS `32f5009a…`, 7,055 entries, rc 0) alongside the
  result md, and record the shas. Minor formatting: 7-char kit-tip abbreviation (`7330338…`) vs 8 elsewhere;
  GPU cell "(TASL-2 4090)" vs "(card n)" elsewhere.
- **m7 — licence/availability cell (line 21).** "option A CPU transport" is methodology, not licence; and
  availability is missing. Per U1 §7 write e.g. "autoresearch code MIT declared in README (no LICENSE file);
  climbmix dataset MIT declared on the HF card (uploader assertion); public/HTTP 200; data present
  (963 M, manifest `ab7186d2…`)", and put the option-A transport note elsewhere or drop it.
- **m8 — "one accepted unit and one smoke per node (no retry)" (lines 3–8) needs the AR nuance.** For AR the
  **executed** unit is the TASL-2 **amended** unit (`b83d9159…`, 74 lines, committed at `d65079af`), while the
  reviewed unit is `3bb015a1…` (56 lines, recorded only in the unit review); the node also had the 20 Nov
  STOP and the 21 Nov retry STOP before the TASL-2 smoke. Say "one executed smoke on TASL-2, no retry within
  the TASL-2 session; earlier Ada attempts/retry STOP preserved".
- **m9 — title/date and the superseded addendum.** The title still says "20 November 2026" while the census
  now carries a 21 Nov row; record the update date and this revision's sha/delta in the header (acceptance
  will bind to `8c0c0173…`). The committed `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` (`fa7bb75d…`) still says
  "No U4 measured row or accepted number changes: autoresearch remains blocked and is not a U4 row"; mark it
  superseded (or add a census note) so the record trail is not self-contradictory.
- **m10 — R5 conditions not closed/recorded.** The R5-accepted census's carried documentation conditions
  (C2–C10 in `9c604f1b…`) remain open — duplicate fix-review filename, licence column vs U1 §7, incomplete
  citations, imdb verbatim sentence, CPU/RAM wording — and this update adds to the citation debt (m5). They
  were allowed as recorded conditions, but the update should record that they remain open (or close them) so
  the final census is not committed with unrecorded conditions.
- **m11 — the U2 row is admitted while the cited U2 result's own acceptance conditions are not fully applied**
  (see §5). This is a dependency on the AR evidence, not a census-number defect; the census should cite the
  conditional acceptance and the residual items rather than an unqualified "accepted".

## 5. Dependency record — status of the AR U2 result review's conditions C1–C5 (claimed applied)

The lead's task states the U2 result review's C1–C5 are applied. Checked against the delivered bytes:

| condition | status | evidence |
|---|---|---|
| **C1** executed-unit record | **NOT fully applied** | The U2 result (`4689c673…` lines 10–13) cites the reviewed-unit sha `3bb015a1…` and says the executed amended unit "is preserved as `<captures>/references/U2_ISO_AUTORESEARCH_UNIT_20261121.md`". **No such file exists** in the delivered 7,056-file bundle / 7,055 SHA256SUMS entries, and the amended-unit sha **`b83d9159…`** is cited neither there nor anywhere except the review. The committed amended unit exists at `docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md` (`b83d9159…`, 74 lines); the reviewed 56-line object `3bb015a1…` is not preserved. |
| **C2** land the census/U4 update | **partial** (this census update) | The row is landed, but the C2 list's whole-smoke wall **1,791.0 s**, **3.176×**, worker peak **1,980.1 MB** and cgroup peak **5.17 GiB** are not recorded in the census (§MAJOR-2). |
| **C3** host-check C1–C4 + author-row record | **NOT applied** | `TASL2_ISOLATION_HOST_CHECK_20261121.md` is byte-unchanged at `0a1fa3a4…` (the reviewed object), so host-check review C1–C4 were not applied; `R1-TRACKG-AR-U2-TASL2` (and the lead delegation) still appears only in reports/captures, not in committed `docs/r1/PLAN.md` or a preserved record-trail file. |
| **C4** report accuracy (m4–m12) | **partial** | Applied: 20,000 MiB floor disclosed, `s001` 166,300 B, bundle-content 152,751,278 B, false-STOP empty-stderr wording, no-evidence/no-noise/no-D21–D28/no-T1 statement. **Not applied**: parent peak **`AR_INFO parent_peak_vram_mb=6560.3`** (in `s000_baseline/run.log`) is still absent from both reports; the smoke report still says "median 218.951 s" (that is the upper middle of 8 executed; the arithmetic median is 218.7935 s), and the U2 result's new "B1/B2 median 218.7935 s" is itself mislabelled (218.7935 is the **8-executed-run** median, not the B1/B2 median, which is 218.697); the 1,791.0 s "(29:49)" shorthand is only partly corrected (1,791.0 s is 29:51; 29:49.26 = 1,789.26 s). |
| **C5** verification integrity | **satisfied** | One smoke, no re-run; smoke report `8814eecc…` and captures `32f5009a…` unchanged and correctly cited; verifier rc 0 / `issues:[]`. |

Also: the reviewed U2 result object `ca3bcadd…` is **not preserved**; the current `4689c673…` was amended
after the review and has **not** been re-reviewed, and the census cites it as "accepted" without recording the
new sha. Re-apply C1/C3/C4 and record the new sha/delta (or re-review) before the AR row is treated as final
evidence. No re-run is required or permitted.

## 6. Conditions (documentation/record only — no new run, no measurement/record edit)

- **C1 (MAJOR-1).** Rewrite the per-suite appendix autoresearch bullet (lines 59–61) to the post-TASL-2 state,
  consistent with the row and the Blocked bullet: passed on TASL-2 under `R1-TRACKG-AR-U2-TASL2`; host
  difference and gate/floor substitutions disclosed; earlier 20 Nov failure + 21 Nov retry STOP preserved as
  superseded external-contention evidence; no node blocked. Remove "not in this census".
- **C2 (MAJOR-2).** Integrate the AR row into the run-level facts: add the AR run-level row (whole-smoke max
  RSS 3,204,520 kB; deployed pin `ca049086…` 21 entries; gate `gate/gate_not_applicable.txt`;
  disk 388,531,040,256 → 388,344,332,288 B; co-tenant monitor 879 ticks/0 foreign apps) or an explicit
  eight-row/AR-exception statement; change "All seven rows" to eight with the AR exceptions; state that the
  Paper-A three-check gate was **NOT APPLICABLE** on TASL-2 and that exclusivity controls substituted for it,
  and that the 40 GiB floor was replaced by 20,000 MiB. Optionally carry C2's wall/3.176×/worker/cgroup-peak
  figures.
- **C3 (m2 + §5).** Qualify "accepted" as **conditional on C1–C5 (report-only)**, cite the review sha
  `9de24ec5…`, and record the current U2 result sha `4689c673…` plus the reviewed-object sha `ca3bcadd…`
  delta. Apply (or record as open) the U2 review's C1/C3/C4 residuals: amended-unit sha `b83d9159…` and a
  real preserved copy (the claimed `<captures>/references/U2_ISO_AUTORESEARCH_UNIT_20261121.md` is absent —
  do not assert it); host-check C1–C4 + the author row in the record trail; parent peak 6,560.3 MB; median
  label; 1,791.0 s/29:49.
- **C4 (m3/m4).** Name the comparison baseline (17 Nov Ada un-isolated U2, 67.901 s / 1.291068 / L40S) and
  qualify 3.225× as a cross-host composite (option A + host change; bpb/VRAM not normalised) and 0.2345 s as
  a surrogate; disclose the TASL-2 gate/floor/env adaptations; restore the 20 Nov STOP and 21 Nov retry STOP
  record paths and shas as historical evidence.
- **C5 (m5/m6/m7).** Complete the authority/acceptance citations (AR result review, host-check
  report/review, `R1-TRACKG-AR-COND7` `:1317`, `R1-T1-HOST-H200` `:1329`, G3-EARLY at
  `94db94bb`/`origin/main` not `de3de54f`, the author-signed TASL-2 row provenance, the U2 result/smoke/
  captures shas); fix the record cell to the record directory + shas; fix the licence/availability cell per
  U1 §7; close the R5 C6 residuals.
- **C6 (m1/m8/m9).** Update readiness to "autoresearch joins now per G3-EARLY, subject to the author row
  landing and the U2 acceptance conditions" and drop/qualify "all eight rows are now complete"; add the
  one-TASL-2-smoke/no-retry nuance; record the 21 Nov update date/revision; mark
  `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` superseded (or reference it).
- **C7 (m10).** Record that the R5 carried conditions C2–C10 remain open (or close them) so the census is not
  committed with unrecorded conditions.
- **C8 (traceability).** Bind acceptance to census SHA-256 `8c0c0173…` and commit the census together with its
  cited AR evidence (U2 result `4689c673…`, smoke report `8814eecc…`, captures `SHA256SUMS` `32f5009a…` —
  7,055/7,055 rc 0, host check `0a1fa3a4…`, U2 result review `9de24ec5…`, host-check review `bfe9b231…`),
  recording the shas; the row's 15 values are verified and must not change. If any cited report text changes,
  record the new sha. No re-run, no smoke, no measurement/record edit is required or permitted by this
  review.

## 7. Acceptance binding and read-only attestation

Acceptance would bind to the reviewed content `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`,
SHA-256 `8c0c0173ae47980985a35ec6992230532c5714461582374153c62c8d8168c54c`, 101 lines / 10,251 bytes, mtime
2026-11-21T03:47:56Z, tracked-modified at HEAD `ebe03cd5` (prior accepted blob `6d1ac47f…` = `146b1114…`
preserved). The verdict is **NOT ACCEPTED** because of MAJOR-1 and MAJOR-2 (report/status text only); the
measured AR row is correct. **Written:** only this review file. **Read-only:** all cited files and captures
above; `shasum -a 256` / `shasum -a 256 -c` (captures 7,055/7,055 rc 0); JSON parses of the AR records,
`verify_full.json`, `sampler_max.json`, `data_manifest.txt`, `pins*`, `time_v.txt`, `disk_*`,
`gate/gate_not_applicable.txt`; `git rev-parse/log/diff/status/ls-tree/show`; `wc`, `stat`, `grep`, `sed`,
`pandoc -f gfm` render check. **Not done:** no run, smoke, U2/GPU/T1/census job, probe, SSH, live-host
inspection, file edit outside this review, commit, push, deletion/move, HTCondor/deepthought action, or
secret/credential read. No other review's object was modified.
