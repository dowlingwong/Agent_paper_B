# Independent final review (round 3) — Track G U4 census AR-row update after R2 conditional acceptance (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-ar-row-reviewer-r3`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2/TASL-7 host checks, the AR unit/result/smoke, the U4 census, or the
earlier U4 reviews (R1–R5 and the round-1/round-2 AR-row reviews). **Read-only:** the only file written is this
review (untracked; no commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or live-host contact, edit of
any other file, deletion/move, HTCondor or deepthought action. Every fact below is recomputed from the delivered
local bytes or read from local git/records.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`79ad29caf56805cff375ef04dfed897b21ecc2b92c7d2a6a289be9479ebc7f26`**, **123 lines / 12,634 bytes**, mtime
**2026-11-21T04:10:14Z**, **tracked and modified** in the worktree at HEAD **`ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`**
(`origin/ops-tasl-20261116` = same; `origin/main` = `4aac5209`). The HEAD blob is `6d1ac47f…` = SHA-256
`146b111410122108c7efa25246b61db62060adcaa3ea14fb2111ec2e13d692d7`, 109 lines, i.e. the R5-accepted/C1-repaired
census committed at `76f1d7ba`; the working-tree delta vs HEAD is **+39/−25 lines** and touches only the eighth
row, the run-level AR row and the "All eight rows" sentence, the per-suite autoresearch bullet, the new "AR row
measurement notes" paragraph, the Blocked/readiness text and the citations section. The seven earlier rows, the
funnel appendix, kitchen/environment and licence paragraph are byte-identical to the HEAD blob.

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_R2_20261121.md` SHA-256
**`5fe423ac8d5aaa79cb62c2eee0ae9c0a2ed3c6c20a11913c1dbdfb51ca1e79fa`** (328 lines) — **ACCEPTED, 0 BLOCKING,
0 MAJOR, 12 MINOR, 1 traceability note, conditions C1–C8**, with **C1 and C2 mandatory before commit**. Its object
(`76bf88db…`, 115 lines / 11,734 B) was overwritten in place at 03:59:34Z and is not preserved, so the
round-2→round-3 delta is audited against R2's verbatim quotes plus the HEAD diff, not byte-for-byte (traceability
note t1).

**Inputs / authority read (all local, read-only; no live host was contacted).** The AR U2 result
`U2_ISO_AUTORESEARCH_RESULT_20261121.md` SHA-256 **`c03f0cbdef8a1799f959ae240df89c84caa8dac2777e2728e77032765fe2a34b`**,
67 lines / 5,204 B, mtime **04:10:14Z** (R2 recorded the then-current object `8430854c…`, 67 lines / 5,181 B;
the reviewed object `ca3bcadd…` is not preserved); the executed-unit sibling copy
`U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` **`b83d91597eaf665b942f4f02fd30f149da53f5f1cc0e6579d1e6711669734432`**
(74 lines / 6,374 B, byte-identical by `diff` to the committed Ada-targeted unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md`, committed `d65079af`); the U2 result
review `U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` **`9de24ec5ebd38825b4f352deeeb7df6a9b5f2d0d1890258119bc2368b4c16aaa`**
(212 lines; **ACCEPTED — 0 BLOCKING, 1 MAJOR report-only, 12 MINOR, conditional on C1–C5**); the smoke result
`TASL2_AR_COND7A_RESULT_20261121.md` **`8814eecc1fb0f9ded4920adc15aa276a05c08e5a181a0a1ed4c5d564f088d0ad`** (288 lines
/ 22,667 B, **PASS**) and its captures `TASL2_AR_COND7A_RESULT_20261121_captures/` (`SHA256SUMS` **`32f5009a…`**,
7,055 entries, 7,056 regular files + 17 symlinks, `shasum -a 256 -c` **rc 0 / 7,055 OK**); the TASL-2 host-check
report **`83636c039fcb7d503abb15468cf4588ebd6795588012b44f6d8f79470d7a5bb6`** (mtime 04:00:26Z) and review
**`bfe9b231…`** (**ACCEPTED** for the AR option-A gate, C1–C4); the TASL-7 host-check report
**`2b703226…`** and review **`18e261cd…`** (**ACCEPTED** for the AR option-A host-gate purpose on TASL-7, C1–C4);
the unit review `TRACKG_U2_ISO_AUTORESEARCH_UNIT_REVIEW_20261121.md` **`ef42276d…`** (reviewed unit `3bb015a1…`,
not preserved); the code review/report `261a03e9…` / `370782ab…`; R5 review `9c604f1b…` (object `4e050ad2…`);
the committed addendum `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` **`fa7bb75d…`** (HEAD); `docs/r1/PLAN.md` at HEAD
(1,337 lines, sha `7e0e160a…`; `R1-TRACKG-AR-COND7` :1317, `R1-T1-HOST-H200` :1329, `R1-TRACKG-G3-EARLY` :1330);
`U1_LICENCE_AVAILABILITY_20261117.md`; and the AR captures parsed directly (9 `run_record.json` = 8 executed +
refused `s001`; `time_v.txt`; `disk_before/after.txt`; `pins*.txt`; `data_manifest.txt`; `sampler/sampler_max.json`;
`slowdown.json`; `memory_cgroup.txt`; `gate/gate_not_applicable.txt`; `verify_full.json`; `kit.txt`; `facts.json`;
`RESULT_STATUS*`; `references/`). The census was cell-counted and `pandoc -f gfm` render-checked.

**Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 11 MINOR, 1 traceability note, conditional on C1–C5 below
(documentation/record only; no re-run, no measured-value change).** **R2's two mandatory items C1 and C2 are
closed in substance:** the false "executed unit in the captures" provenance and the unconditional "C1–C5 applied"
wording are gone; the executed-unit sibling `b83d9159…` and the un-preserved reviewed unit `3bb015a1…` are now
correctly recorded; the U2 acceptance is now "ACCEPTED **conditional on C1–C5**" with the review sha
`9de24ec5…`; the gate-capture path is fixed to the `_captures/` directory; the parent peak `6,560.3 MB`, the
20,000 MiB floor, env `ar-cond7a` and data root are disclosed; the addendum is marked superseded; and the title
carries the 21 Nov row date. **No new MAJOR/BLOCKING was found and no fabricated or overclaimed measured value
was found.** The remaining defects are **record/citation accuracy** (host-check reviews are cited by the wrong
file names; the U2 result's post-review sha and the open U2-review residuals are not recorded; "each row's gate
JSON" is still false for the AR row; "no retry" is still unqualified; the record/licence/host-caveat cells and the
R5 carried conditions remain open) — the same documentation class R2 carried as C3–C8.

---

## 1. Closure of R2's mandatory C1/C2 and its m1–m3

### 1.1 R2 C1 / m1 (executed-unit provenance) — **CLOSED in substance; one precision residual**

The R2 objection was that the census said the executed amended unit was "in the captures". The current text at
`:63` and `:74–76` says:

> "…C1–C4 text conditions are partially applied (executed sibling unit copy
> `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` sha `b83d9159…`; reviewed `3bb015a1…` not preserved; parent peak
> 6,560.3 MB recorded in the U2 result)."

The false captures assertion is gone; the sibling copy and its sha are cited; the reviewed unit's non-preservation
is recorded. Verified: (i) the sibling file exists with sha `b83d9159…`, 74 lines / 6,374 B, and `diff` shows it
byte-identical to the committed unit; (ii) the captures bundle contains **no** unit copy — `references/` holds six
files (retry result, TASL-2 host-check report/review, code unit, 17 Nov result, 20 Nov result) and a `grep` of the
7,055-entry `SHA256SUMS` finds no `U2_ISO_AUTORESEARCH_UNIT` entry and no `b83d9159`/`3bb015a1`; (iii) `3bb015a1…`
is not preserved (only the unit review and the U2 result text cite it). Residual (m1): the census still does not
record that the sibling copy is byte-identical to the **committed Ada-targeted** unit (Host Ada, `envs/torch312`,
Ada data root, Paper A gate, ≥40 GiB floor), so the TASL-2 adaptations exist only as the U2 result's declared
deviations; nor that it is explicitly not in the captures; nor its 74-line size.

### 1.2 R2 C2 / m2 (U2 acceptance overstatement) — **CLOSED in substance; traceability sub-items remain**

R2 objected that the census said "review ACCEPTED, C1–C5 applied". The current text says "result review ACCEPTED
**conditional on C1–C5**; C1–C4 text conditions are partially applied" (`:63`) and "review conditional C1–C5"
(`:74`), and cites review `9de24ec5…` (`:118–119`). This correctly qualifies the dependency and matches the U2
review's actual verdict (`ACCEPTED — 0 BLOCKING, 1 MAJOR report-only, 12 MINOR, conditional on C1–C5`) and its §5
status table (C1 partially, C2 applied, C3 not applied, C4 partially, C5 satisfied). Residual (m2): the census
does **not** record (a) the current U2 result sha `c03f0cbd…`, (b) the reviewed object `ca3bcadd…` (not preserved)
nor the R2-recorded interim `8430854c…`, (c) the post-review edit — see §4 below, (d) the open C3/C4 residuals as a
list, or (e) where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved.

### 1.3 R2 m3 (citations still pre-AR) — **PARTIALLY fixed; the added host-check citation is misattributed**

The citations section (`:109–123`) now names the AR U2 result review with sha `9de24ec5…`, replaces "six isolated
U2 result reviews" with "three result reviews covering the six earlier torch nodes + HousePrice result review +
AR U2 result review", and adds a "TASL-2/TASL-7 host-check reviews" clause. But the two files it names in that
clause — `TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` and `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` — are
the **five-node result review** and the **Breakout result review**, not host-check reviews (titles checked). The
actual reviews are `TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`bfe9b231…`) and
`TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`18e261cd…`); the reports are `83636c03…` (TASL-2, amended
04:00:26Z) and `2b703226…` (TASL-7). Still absent: the AR result sha `c03f0cbd…`, smoke `8814eecc…`, captures
`32f5009a…`, code review/report `261a03e9…`/`370782ab…`, `R1-TRACKG-AR-COND7` PLAN :1317 and `R1-T1-HOST-H200`
PLAN :1329 in the citations (the latter appears only in the readiness body), and the author-row provenance. The
"three result reviews covering the six earlier torch nodes + HousePrice result review" phrasing also double-counts
the HousePrice review. This is m3 below.

## 2. Mechanical / integrity checks (all pass; no formatting regression)

- Main table: header, delimiter and **all 8 data rows = 15 cells each**. Run-level table: header, delimiter and
  **all 8 data rows = 5 cells each**. `pandoc -f gfm -t html` emits two tables, 18 `<tr>` (9+9) and 20 `<th>`
  (15+5); no broken pipes.
- Working-tree diff vs HEAD is **+39/−25** and touches only AR/readiness/citation text; the seven earlier rows,
  their run-level rows, the funnel appendix, kitchen/environment and licence paragraph are byte-identical to the
  R5-accepted HEAD blob `146b1114…`, so their measured values are unchanged and remain covered by R5.
- AR captures: `SHA256SUMS` sha `32f5009a…`, **`shasum -a 256 -c` → rc 0, 7,055/7,055 OK** (7,056 regular files,
  17 symlinks); 9 `run_record.json` = 8 executed + refused `s001`; `verify_full.json` `ok:true`, `issues:[]`,
  `ipc_hits:[]`, `no_cuda_ipc_error:true`, 9 records / 8 executed / refused `s001`; `CHECKLIST_E_PASSED`; no
  synthetic marker; one `systemd-run` scope; no second AR evidence root (U2 review §1).
- All seven earlier rows' record directories and gate JSONs exist; every gate JSON is `verdict:"clear_finished"`,
  `paper_a_live_waiting_for_card:false`, `evidence.gpu.paper_a_processes:[]`, UTC-stamped (spot-checked all 7).
  The AR row has **no gate JSON** — only `gate/gate_not_applicable.txt` (`paper_a_gate=NOT_APPLICABLE_ON_TASL2`,
  0 compute apps at launch, exclusive `flock`, 1 s sampler, co-tenant abort monitor, 879/879 ticks foreign=[]).

## 3. AR row — all 15 cells re-verified from the records (none taken from the census)

| # | cell | census value | verified against | result |
|---|---|---|---|---|
| 1 | node | `autoresearch_fixedtokens` | run records / U2 result | ✅ |
| 2 | suite | `autoresearch` | U1 §2; smoke report | ✅ |
| 3 | kit tip | `7330338…` | `kit.txt` `tip=7330338…`; tracked-clean; merge-bases yes | ✅ (7-char form, m7) |
| 4 | B1 elapsed | `218.951 s` | `runs_smoke/s000_baseline` `elapsed_seconds_info_only` | ✅ |
| 5 | B1 metric | `1.293937 (val_bpb)` | same record `outcome.value`; `verify_full.B1_seconds` | ✅ |
| 6 | B2 elapsed | `218.443 s` | `runs_edits/B2` | ✅ |
| 7 | B2 metric | `1.293937 (val_bpb)` | identical to B1 (exact repeat) | ✅ |
| 8 | sealed test | `n/a` | `sealed` is `{}` / verifier `sealed_key:null` in every record | ✅ |
| 9 | timeout = 3×B1 | `656.853 s` | 3 × 218.951 = 656.853 (same rule as the seven rows) | ✅ |
| 10 | whole-smoke upper bound | `12,436 MiB` | `sampler_max.json` `whole_smoke_upper_bound_mib:12436`, labelled upper bound | ✅ |
| 11 | GPU/cpus | `GPU-4d623e76…` (TASL-2 4090), cpus 0-7 | every record `limits.gpu_uuids`/`cpu_list`; `cgroup_probe.txt` | ✅ |
| 12 | committed-file pin | `147f0d35…` | `prep/pins_committed.txt` (20 entries), `pins.txt` | ✅ |
| 13 | data manifest sha256 | `ab7186d2…` | `data_manifest.txt` (expected == observed; 13 manifest files, 963 M) | ✅ |
| 14 | record | `U2_ISO_AUTORESEARCH_RESULT_20261121.md` | file exists; captures dir exists | ✅ exists; captures sha missing (m7) |
| 15 | licence/availability | `autoresearch MIT/climbmix MIT-claimed; option A CPU transport` | U1 §7: code MIT declared in README (no LICENSE file); climbmix MIT declared on HF card | ✅-ish (m8) |

No 17 Nov un-isolated value (67.901 s / 5,211.3 MB / 1.291068) is used as a TASL-2 row value. The row is a real
isolated option-A TASL-2 measurement: every executed record `isolation.effective:true`, `waivers {}`,
`exceptions []`, private `/dev/shm`, no CUDA IPC (calls are `iso.SharedBuffer` CPU `memfd`; the `cuda_share`/
`cuda_open` helpers remain defined-but-unused in `ar_isolated.py`), cgroup `memory.max=8589934592`,
`memory.swap.max=0`, `cgroup.kill` exposed; `B1/B2` exact `val_bpb`; slowdown measured. **No fabricated value was
found in the AR row.**

## 4. Run-level facts, AR notes and the post-review U2-result edit

- Run-level AR row: max RSS **3,204,520 kB** (`time_v.txt` `Maximum resident set size: 3204520`); deployed pin
  `ca049086…` (21 entries incl. data link; Ada value `069e987a…` correctly not expected); gate capture path now
  **`TASL2_AR_COND7A_RESULT_20261121_captures/gate/gate_not_applicable.txt`** — fixed from R2's malformed
  `…RESULT_20261121.md/gate/…`; disk **388,531,040,256 → 388,344,332,288 B** (`disk_before/after.txt`; the
  `RESULT_STATUS.txt`/`facts.json` value `388,344,274,944 B` differs as R2 already noted — the census consistently
  uses the `disk_*` capture pair).
- AR measurement notes reproduce: wall **1,791.0 s** (lease 01:58:19→02:28:10Z; `/usr/bin/time -v` 1,789.26 s /
  29:49.26; 1,791/564 = **3.176×**); worker peak **1,980.1 MB** (baseline/B2/s002/s003/E1/E3), max run **3,720.4 MB**
  (E2); parent peak **6,560.3 MB** (run log `AR_INFO parent_peak_vram_mb=6560.3`); cgroup peak **5.17 GiB**
  (`memory.peak 5,550,911,488 B`; events max/oom/oom_kill 0; swap.max 0); sampler upper bound **12,436 MiB** (not
  per-run); committed pin `147f0d35…` (20 entries) / deployed `ca049086…` (21); CPU `memfd`, no CUDA IPC;
  one clean smoke is the U2 measurement, no second U2 run.
- **Post-review U2-result edit (traceability).** The U2 result is now `c03f0cbd…`, 67 lines / **5,204 B**, mtime
  04:10:14Z; R2 recorded `8430854c…`, 67 lines / **5,181 B**. The +23 B delta and unchanged line count are
  consistent with the inserted parent-peak clause now at `:36` ("parent peak 6,560.3 MB"), which is exactly the
  U2 review C4/m5 item R2 recorded as not applied; the current text is therefore the source of the census's
  parent-peak claim. The old bytes are not preserved, so this delta cannot be audited byte-for-byte — it must be
  recorded (m2/t1). The U2 result still carries the R2-noted residuals the census's "partially applied" wording
  describes: `:43` "B1/B2 median 218.7935 s" (218.7935 is the median of the 8 executed runs, not of B1/B2) and
  `:45` "1,791.0 s (29:49)" shorthand (the `time -v` 1,789.26 s is given separately at `:49`). These are U2-result
  text residuals, not census-value errors.

## 5. All eight rows, and U4 vs G.1b/G.4

- **Seven earlier rows:** byte-identical to the R5-accepted HEAD blob `146b1114…`; record directories and gate JSONs
  verified present and `clear_finished`/`paper_a_processes []` (all 7 checked programmatically); their measured
  values are therefore unchanged and remain covered by R5's acceptance. **AR row:** all 15 cells verified above;
  run-level facts verified; captures
  7,055/7,055 OK. No row was dropped and no measured value changed in this revision.
- **U4 no longer blocks G.1b/G.4 — confirmed.** `R1-TRACKG-G3-EARLY` (`PLAN:1330`) sets the six earlier nodes for
  G.1b/G.4 now, with HousePrice/autoresearch joining as soon as their U2 passes; `R1-T1-HOST-H200` (`PLAN:1329`)
  keeps the T1 labels on H200. The census's readiness text (`:103–106`) says all eight rows are complete, the
  census does not block G.1b/G.4 and is not evidence; the AR row is an ENGINEERING_ONLY U2 raw-cost row (not T1).
  The author-signed `R1-TRACKG-AR-U2-TASL2` row is correctly flagged as not yet in committed `PLAN.md` (verified:
  absent at HEAD and `origin/main` `4aac5209`; it appears only in the reports) and "reaches main after the sweep-2
  launch" is a report claim (m11).

## 6. Remaining findings — all MINOR (documentation/record; no measured value affected)

- **m1 — executed-unit precision (R2 C1 residual).** `:63`, `:74–76` cite the sibling copy `b83d9159…` but do not
  state that it is byte-identical to the committed **Ada-targeted** unit (so the TASL-2 adaptations exist only as
  the U2 result's declared deviations), that it is **not** in the captures, or that it is 74 lines. No false claim
  remains; the precision required by R2 C1 is incomplete.
- **m2 — U2 result version/traceability (R2 C2 residual).** The census cites the U2 result only by filename
  (`:21`, `:74`, `:94`); it does not record the current sha `c03f0cbd…`, the reviewed `ca3bcadd…`/R2-recorded
  `8430854c…` non-preservation, or the post-review parent-peak edit; nor the open U2-review C3/C4 residuals as a
  list; nor where the author-signed row/delegation is preserved.
- **m3 — citations incomplete/misattributed (R2 C3).** The "TASL-2/TASL-7 host-check reviews" parenthetical names
  two result reviews (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md`, `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`)
  instead of `TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`bfe9b231…`) and
  `TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md` (`18e261cd…`); the host-check report shas (`83636c03…`,
  `2b703226…`), AR result `c03f0cbd…`, smoke `8814eecc…`, captures `32f5009a…`, `R1-TRACKG-AR-COND7` :1317 and
  `R1-T1-HOST-H200` :1329 are absent from the citations, and "three result reviews covering the six earlier torch
  nodes + HousePrice result review" double-counts the HousePrice review.
- **m4 — "each row's gate JSON is `clear_finished`…" (`:36–38`) is false for the AR row (R2 C4 residual).** The
  AR row has no gate JSON, only `gate_not_applicable.txt`; the sentence needs an AR qualifier. The malformed path
  itself is fixed (verified).
- **m5 — "no retry" still unqualified (`:7–8`, `:40`) (R2 C5/m6).** The census discloses the 20 Nov Ada co-tenant
  OOM and the 21 Nov retry session (0 run records) at `:63–64`/`:96–97`, yet still says "one accepted unit and one
  smoke per node (no retry)" and "one unit, one executed smoke, no retry". Qualify as "one executed TASL-2 smoke,
  no retry within the TASL-2 session; the earlier Ada attempt and the 21 Nov retry session are preserved
  external-contention STOPs", and disclose that the single clean smoke serves as both the pre-U2 gate and the U2
  run.
- **m6 — TASL-2 adaptations/comparison labels incomplete (R2 C4/m5).** `:94` still says "one host difference
  TASL-2/4090 vs the earlier Ada attempt" (should name the 17 Nov Ada **un-isolated** U2 and the
  host+env+data-root+20,000 MiB-floor+no-Paper-A-gate substitutions); `:95` "3.225× cross-host option-A slowdown"
  should be labelled a composite (option A + host change; bpb/VRAM not normalised); `:95` "transfer 0.2345 s/request"
  should be labelled a wall-clock surrogate.
- **m7 — record cell and formatting (R2 C6/m8).** The AR `record` cell (`:21`) cites only the U2 result report;
  every other row cites a record directory and no captures sha is given. Cite
  `TASL2_AR_COND7A_RESULT_20261121_captures/` (`SHA256SUMS` `32f5009a…`, 7,055/7,055 OK) beside the result.
  Formatting: 7-char kit tip `7330338…` vs 8 elsewhere; GPU "(TASL-2 4090)" vs "(card n)" elsewhere.
- **m8 — licence/availability cell (R2 C6/m9).** "option A CPU transport" is methodology, not licence; availability
  is missing. Per U1 §7: code MIT declared in README (no LICENSE file), climbmix MIT declared on the HF card
  (uploader assertion), public/HTTP 200, data present (963 M, manifest `ab7186d2…`).
- **m9 — host-check caveat (R2 C6/m10).** `:93` "TASL-2 host checks PASS/accepted" should say "for the **AR
  option-A gate only**; §3 item 7 CUDA IPC remains **UNTESTED**; `HARNESS_ISOLATION` §5 item 5/§5.5 open; no
  `cuda_share`/`cuda_open` node may start on its strength" (the new `:111–113` "CUDA IPC is not tested" partially
  covers item 7).
- **m10 — R5 carried conditions / revision line (R2 C7/m12).** The title now carries the 21 Nov row date but no
  revision sha/line. R5's documentation conditions (C4 duplicate fix-review name — still duplicated at `:83–84`;
  C5 licence column; C6 citations; C7 imdb sentence; C8 CPU/RAM wording; C9 preserve revision; C10 commit AR
  evidence) remain unrecorded as open/closed.
- **m11 — authorizations/completion qualifiers (R2 C2/m11).** "author-signed `R1-TRACKG-AR-U2-TASL2`" and
  "reaches main after the sweep-2 launch" are report claims not in committed PLAN (flagged as "not yet in
  committed PLAN at review time" at `:104`, good); "All eight rows are complete" (`:105`) is not qualified with the
  U2 review's conditional C1–C5 or the ENGINEERING_ONLY raw-cost status (the "is not evidence" clause covers part).
- **t1 — traceability (not a finding against a value).** R2's object (`76bf88db…`) was overwritten in place and is
  not preserved (only R2's review cites it); the U2 result also changed after review (`8430854c…` → `c03f0cbd…`).
  Bind this acceptance to census sha `79ad29ca…` and preserve it by committing the census (with the cited AR
  evidence, see C5); record the deltas.

## 7. Conditions (documentation/record only — no new run, no measurement/record edit)

- **C1 (before commit; m1/m2/t1).** Record the current U2 result sha `c03f0cbd…` and that the reviewed
  `ca3bcadd…` / R2-recorded `8430854c…` are not preserved, including the post-review +23 B parent-peak insertion;
  list the open U2-review C3/C4 residuals; complete the executed-unit precision (sibling `b83d9159…` is
  byte-identical to the committed Ada-targeted unit, 74 lines, **not** in the captures; TASL-2 adaptations exist
  only as the U2 result's declared deviations); record where the author-signed row/delegation is preserved.
- **C2 (before commit; m3).** Correct/completing the citations: TASL-2 host-check report `83636c03…` + review
  `bfe9b231…`; TASL-7 host-check report `2b703226…` + review `18e261cd…`; AR U2 result `c03f0cbd…`; U2 review
  `9de24ec5…`; smoke `8814eecc…`; captures `32f5009a…` (7,055/7,055); code review/report `261a03e9…`/`370782ab…`;
  `R1-TRACKG-AR-COND7` (`PLAN:1317`) and `R1-T1-HOST-H200` (`PLAN:1329`); fix the result-review count/phrasing and
  the host-check-review names.
- **C3 (m4/m5/m6).** Qualify the "each row's gate JSON" sentence for the AR row; qualify the two "no retry"
  statements and disclose the single-smoke-as-pre-U2-gate arrangement; disclose the full TASL-2 substitution list
  and name the 17 Nov Ada un-isolated baseline; label 3.225× as a cross-host composite (option A + host change,
  bpb/VRAM not normalised) and 0.2345 s as a wall-clock surrogate.
- **C4 (m7/m8/m9).** Add the captures dir + `SHA256SUMS` sha to the record cell; complete the licence/availability
  cell per U1 §7; add the host-check caveat (AR option-A gate only; item 7 UNTESTED; §5 item 5/§5.5 open; no
  `cuda_share`/`cuda_open` node on its strength; cite the amended `83636c03…` report as the successor of the
  reviewed `0a1fa3a4…`).
- **C5 (m10/m11/t1).** Record R5's carried conditions as open (or close them) and remove the duplicated
  fix-review filename; add a revision line with the 21 Nov date/sha; qualify "All eight rows are complete";
  **bind acceptance to census SHA-256 `79ad29ca…`** and commit the census together with the cited AR evidence
  (`U2_ISO_AUTORESEARCH_RESULT_20261121.md` `c03f0cbd…`, unit copy `b83d9159…`, smoke `8814eecc…`, captures
  `32f5009a…`, U2 review `9de24ec5…`, host checks + reviews, retry/20 Nov references), recording the shas and
  preserving the accepted revision. The AR row's 15 values are verified and must not change; no re-run, no smoke,
  no second U2, no measurement/record edit is permitted or required by this review.

## 8. Acceptance binding and read-only attestation

Acceptance binds to the reviewed content
`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`79ad29caf56805cff375ef04dfed897b21ecc2b92c7d2a6a289be9479ebc7f26`**, 123 lines / 12,634 bytes, mtime
2026-11-21T04:10:14Z, tracked-modified at HEAD `ebe03cd5` (HEAD blob `6d1ac47f…` = `146b1114…` preserved). The
verdict is **ACCEPTED with conditions C1–C5**; R2's two MAJORs remain closed, R2's mandatory C1/C2 are closed in
substance, and the measured AR row is correct. **Written:** only this review file. **Read-only:** all cited files
and captures; `shasum -a 256`; `shasum -a 256 -c SHA256SUMS` (captures 7,055/7,055 OK, rc 0); JSON parses of the
AR records, `verify_full.json`, `sampler_max.json`, `slowdown.json`, `memory_cgroup.txt`, `pins*`,
`data_manifest.txt`, `time_v.txt`, `disk_*`, `gate/gate_not_applicable.txt`, all seven earlier gate JSONs;
`git rev-parse/log/diff/status/show`; `wc`, `stat`, `grep`, `diff`, `pandoc -f gfm` render check. **Not done:** no
run, smoke, U2/GPU/T1/census job, probe, SSH/live-host inspection, file edit outside this review, commit, push,
deletion/move, HTCondor/deepthought action, or secret/credential read. No other review's object was modified.
