# Delta-only independent spot-check — Track G U4 census + binding sidecar after R6 NOT ACCEPTED (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u4-delta-spot-check`), delegated by the lead; no involvement in the
autoresearch option-A code/kit, the TASL-2/TASL-7 host checks, the AR unit/result/smoke, the U4 census, the
binding sidecar, or any earlier U4 review (seven-node R1–R5; AR-row R1–R6). **Read-only:** the only file written
in the workspace is this review (untracked; no commit/push). No run, smoke, U2/GPU/T1/census job, probe, SSH or
live-host contact, edit of any other file, deletion/move, HTCondor or deepthought action. Every fact below is
recomputed from the committed objects (`git cat-file`/`git show`/`git ls-tree` on `3c6ce37a`) or from the
delivered local bytes. `shasum -a 256 -c` over the SHA256SUMS file is a read-only integrity check, not a run.

**Scope (delta-only).** This check verifies only the post-R6 delta and the binding pair it produces; it does not
re-audit the seven unchanged census rows beyond byte-identity, and it inherits the accepted seven-node R5 record.
R6's objects are not preserved (see t1), so the R6→final delta is audited against the sizes R6 quoted verbatim.

**Objects under review.**

| object | SHA-256 | size | committed? |
|---|---|---|---|
| census `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md` | **`d7f8f8aab2c4d1002c8f666caca0ae4393ca11514d3d040ac0949f1657c79890`** | **143 lines / 15,267 B** | **yes, at HEAD `3c6ce37a`** |
| binding sidecar `TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md` | **`4212e6caa9b4890d88a00498b27a685b0c1456f8b3b2464e6a1db6aecb1ef341`** | **13 lines / 2,676 B** | **yes, at HEAD** |
| AR U2 result `U2_ISO_AUTORESEARCH_RESULT_20261121.md` | **`8f872f2da42ad6256ac037e5aca267be295d4063edd1ae473e74c7ae47be4d86`** | **76 lines / 5,845 B** | **yes, at HEAD** |
| executed unit sibling `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` | **`b83d91597eaf665b942f4f02fd30f149da53f5f1cc0e6579d1e6711669734432`** | **74 lines / 6,374 B** | **yes, at HEAD** |

**Commit under review.** `3c6ce37a94e1f95cf8f7b322115246209aee79ac` (21 Nov 2026 04:45:13 +01:00),
`origin/ops-tasl-20261116` = `3c6ce37a` (**pushed**); working tree clean before this review (no modified/untracked
files). So the census sha the sidecar binds is commit-reachable.

**Prior round.** `docs/r1/reviews/TRACKG_U4_CENSUS_AR_ROW_REVIEW_R6_20261121.md` — **NOT ACCEPTED, 0 BLOCKING,
3 MAJOR** (record-only traceability: stale U2/census deltas in the binding pair, pair uncommitted/unpreserved,
mis-mapped R5 C4–C10 dispositions), and its condition **C6**: "one more final round (or a documented delta-only
spot-check under the R4/R5 rules)". This file is that documented delta-only spot-check.

**R6→final delta** (R6 object sizes as quoted verbatim in R6 §1/§7; those objects are not preserved, t1):
census `26a30673…` 140/15,045 → `d7f8f8aa…` **143/15,267 (+3 lines / +222 B)**; U2 result `86bdd429…` 76/5,841 →
`8f872f2d…` **76/5,845 (+0 lines / +4 B)**; sidecar `4880b3a0…` 12/2,618 → `4212e6ca…` **13/2,676 (+1 line / +58 B)**.
Cross-check: the sidecar's R3→final and R4→final deltas now exceed R6's computed R3→R6/R4→R6 deltas by exactly
+3 lines/+222 B (the census delta), and the sidecar's reviewed→final is +4 B over R6's +1,948 B (the U2-result
delta). The delta is arithmetically coherent except minor finding m1.

**Verdict: ACCEPTED (delta-only) — 0 BLOCKING, 0 new MAJOR, 3 MINOR (carried), 1 traceability note.** All three
R6 MAJORs are closed in the committed binding pair: the deltas are recomputed and mutually consistent with the
objects they bind, the pair (census + sidecar + U2 result + unit + cited AR evidence) is committed and the sidecar
sha still binding, and the R5 C4–C10 dispositions are correctly mapped with honest open/closed status. The measured
content is unchanged (rows 1–7 byte-identical to the prior committed census; AR row re-verified from committed
captures; captures 7,055/7,055 OK in the delivered tree), no new MAJOR/BLOCKING was found, and U4 still does not
block G.1b/G.4. The three MINORs are record-only and carried (m1: the U2 result's own revision note is 4 B stale;
m2: 49 gitignored hashed capture entries are not commit-reachable, so a fresh checkout verifies 7,006/7,055;
m3: R6 C5 m2/m4/m6/m7 wording residues). Nothing needs re-running; no measured number, pin, manifest, gate,
isolation record or U2 status changes.

---

## 1. Checks that hold

- **Binding is exact and committed.** Sidecar `:6` records census sha **`d7f8f8aa…`** 143 lines / 15,267 B; the
  delivered census rehashes and re-counts exactly so; both are at HEAD `3c6ce37a`. The census has no self-hash and
  defers to the sidecar as the binding record (`:132–142`), which is the only sound design. Sidecar `:7` binds the
  U2 result **`8f872f2d…`** 76/5,845 B; `:9` binds the unit sibling **`b83d9159…`** 74/6,374 B.
- **U2 chain recomputed and consistent.** Sidecar `:8`: reviewed `ca3bcadd…` 57/3,893 → `8430854c…` 67/5,181 →
  `c03f0cbd…` 67/5,204 (+23 B parent-peak = 5,204−5,181) → final 76/5,845, i.e. **+19 lines/+1,952 B** from
  reviewed (76−57; 5,845−3,893) and **+9 lines/+641 B** from `c03f` (76−67; 5,845−5,204) — both arithmetic checks
  pass. Census `:126` states the same figures and the final sha/size, and no stale "current sha" remains.
- **Census-chain deltas recomputed and consistent.** Sidecar `:10`: R3 `79ad29ca…` 123/12,634 → final
  = **+20 lines/+2,633 B** (143−123; 15,267−12,634); R4 `2dbf2c16…` 136/13,984 → final = **+7 lines/+1,283 B**
  (143−136; 15,267−13,984) — both pass; the intermediate U2 step `8430854c→c03f` = +23 B also passes.
  Census `:131–133` states the R3/R4 quoted sizes and defers the exact final sha/lines/bytes and deltas to the
  sidecar (written after it), which now records them; R6 MAJOR-2's stale-delta defect is gone.
- **Eight rows complete and unchanged.** Main table = header + 8 rows at 15 cells; run-level table = header + 8
  rows at 5 cells. Main-table rows 1–7 and run-level rows 1–7 are **byte-identical** to the previous committed
  census at `ebe03cd5:docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md` (blob `146b1114…`, 109 lines /
  10,925 B) — only the AR row was added. No measured value was edited.
- **AR row re-verified from the committed captures** (`TASL2_AR_COND7A_RESULT_20261121_captures/`): B1
  **218.951 s**, B2 **218.443 s**, `val_bpb` **1.293937** both; sealed test `n/a`; timeout **656.853 s** = 3×218.951;
  whole-smoke VRAM upper bound **12,436 MiB** (`slowdown.json`, `sampler/sampler_max.json`); GPU `GPU-4d623e76…`,
  cpus 0-7; committed pin `147f0d35…` (20 entries), deployed TASL-2 pin `ca049086…` (21, path-dependent) —
  `prep/pins_committed_recheck.txt` / `prep/pins_deployed_recheck.txt`; data manifest `ab7186d2…` (13 files, 963 M); record cell cites the U2 result +
  captures dir + `7,055/7,055 OK` + SHA256SUMS `32f5009a…`. Run-level AR row: whole-smoke max RSS **3,204,520 kB**
  (`slowdown.json`/`facts.json`), `gate_not_applicable.txt` present, disk **388,531,040,256 → 388,344,332,288 B**
  (`disk_after.txt`); AR notes: wall **1,791.0 s**, **3.176×** the 17 Nov 564 s smoke (1,791.0/564 = 3.176),
  worker peak **1,980.1 MB**, max run **3,720.4 MB**, parent peak **6,560.3 MB** (recorded in the committed U2
  result `:36`; its raw `run.log` is not commit-reachable — m2), cgroup peak **5.17 GiB** (`facts.json`
  `memory.peak = 5,550,911,488 B`, OOM 0/swap 0), transfer **0.2345 s/request** ((218.951−67.901)/644 = 0.23455),
  slowdown **3.225×** (218.951/67.901 = 3.2245) labelled **cross-host option-A** and the transfer labelled
  **wall-clock surrogate**.
- **Records/isolation unchanged.** 9 AR `run_record.json`: 8 executed (including the divergent `s002`
  `non_finite_loss` record) + refused `s001`; every executed record `isolation.effective:true`, `waivers {}`,
  `exceptions []`; no CUDA-IPC call path; `gate/gate_not_applicable.txt` plus exclusivity substitute; `s001`
  refused size 166,300 B per the U2 result. No re-run, no second U2, one clean smoke.
- **Captures verify in the delivered tree.** `SHA256SUMS` sha **`32f5009a…`**, **7,055 entries**;
  `shasum -a 256 -c SHA256SUMS` → **rc 0, 7,055/7,055 OK** (7,056 regular files + 17 symlinks + 2,128 dirs).
  No capture was edited; the empty/false first STOP artefacts remain (`DONE.initial_false_stop`,
  `RESULT_STATUS.initial_false_stop.txt`). See m2 for the commit-reachability caveat.
- **Authority rows verified.** `docs/r1/PLAN.md` at `origin/main df58bcd5`: `:1258` R1-TRACKG-G0-GO, `:1269`
  R1-TRACKG-LICENCES, `:1289` R1-TRACKG-PORT-DECISIONS, `:1290` R1-HARNESS-ISOLATION, `:1317`
  R1-TRACKG-AR-COND7, `:1329` R1-T1-HOST-H200, `:1330` R1-TRACKG-G3-EARLY — all present with the cited content;
  `de3de54f:PLAN:1258` is R1-TRACKG-G0-GO. The author-signed `R1-TRACKG-AR-U2-TASL2` row is **absent** from both
  committed PLANs (HEAD and `origin/main`), exactly as the census/sidecar disclose.
- **Cited shas all match the delivered files.** smoke `8814eecc…` (288 lines/22,667 B), captures `32f5009a…`,
  U2 review `9de24ec5…` (212/25,629), TASL-2 report `83636c03…` (369/26,031) / review `bfe9b231…` (213/19,408),
  TASL-7 report `2b703226…` (453/32,517) / review `18e261cd…` (270/25,851), superseded addendum `fa7bb75d…`
  (22/1,770), seven-node R5 review `9c604f1b…` (363/36,103), AR-row R4 review `d4c3f9f0…` (255/25,428), R3 review
  `4c5f1848…` (292/26,580), and R6 `87af404d…` (291/28,277). Unit sibling byte-identity re-verified: its sha
  `b83d9159…` equals the committed Ada-targeted unit at `d65079af`/HEAD
  (`docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md`).
- **R5 C4–C10 dispositions are now correctly mapped with honest statuses** (census `:134–139`, sidecar `:11`):
  C4 duplicated fix-review reference removed (closed); C5 licence/availability per U1 §7 partial (licence cell
  added, per-node U1 §7 wording not complete); C6 citations/shas largely closed (minor gaps remain); C7 verbatim
  imdb sentence not applied (partial); C8 CPU/RAM wording partially corrected; C9 binding/preservation via the
  sidecar (sha binding closed; some superseded bytes not preserved); C10 commit of AR evidence/SHA256SUMS caveat
  (see m2). "R5 had 2 MAJOR (not 3)" is corrected; R6 MAJOR-3 is closed.
- **Labels/licence/caveat/scope.** ENGINEERING_ONLY; no evidence/noise floor/D21/D28/T1 label; no
  HTCondor/deepthought; `3.225×` labelled a **cross-host composite** (bpb/VRAM not normalised, `:65`); `0.2345
  s/request` labelled a **wall-clock surrogate** (`:97`); "no U2 retry" qualified by the external-contention
  disclosure (`:8–10`); no CUDA-IPC claim and option A CPU-memfd path only (`:114–115`, sidecar `:13`); T1 labels
  remain H200; no second U2 run; no shared-card launch; data outside repo; author row signed but not in committed
  PLAN at execution. Licence cells and the HousePrice `train.csv` sha256/md5 disclosure are present (U1 §7
  completeness carried open — m3).
- **No dangling citations.** All file-like backticked tokens in the census and sidecar resolve to delivered files;
  the only bare shorthand is `gate_not_applicable.txt` at census `:40`, resolved by the full path at `:36`.
- **U4 no longer blocks G.1b/G.4 — confirmed.** `R1-TRACKG-G3-EARLY` (`:1330`) sets the six earlier nodes for
  G.1b/G.4 now and lets HousePrice/autoresearch join once their U2 passes, "without waiting for the U4 census
  report"; the census readiness text (`:105–108`) says the census does not block G.1b/G.4 and is not evidence.

## 2. R6 MAJOR closure

- **MAJOR-1 (stale U2 chain/deltas; wrong "current" sha) — CLOSED in the binding pair.** Census `:126` now cites
  the final U2 sha `8f872f2d…` 76/5,845 B with the recomputed +19/+1,952 and +9/+641 deltas; sidecar `:8` is
  arithmetically consistent with the object it binds; no `ee21f6d9…`/`+16 lines/+1,591/+280` residue remains in
  the census, sidecar or U2 result. Residual: the U2 result's own revision note still prints R6-era totals (m1).
- **MAJOR-2 (stale census delta; pair uncommitted/unpreserved) — CLOSED.** Census/sidecar deltas recomputed
  (+20/+2,633 and +7/+1,283); sidecar written last (binds the final census sha exactly); census, sidecar, U2 result,
  unit sibling, smoke report, host reports/reviews and the AR capture tree are committed at `3c6ce37a`, so the
  accepted revision is git-preserved (with the m2 capture-entry caveat).
- **MAJOR-3 (mis-mapped R5 C4–C10 dispositions) — CLOSED.** The dispositions list now maps 1:1 to actual R5
  C4–C10 with open/closed statuses that match the content, and does not claim all conditions closed; the sidecar's
  "R5 had 2 MAJOR" count is corrected.
- **No new MAJOR, no BLOCKING.** The measured content is unchanged and independently re-verified; nothing was
  fabricated or overclaimed as a measured value.

## 3. Minor findings (record-only, carried) and traceability note

| # | severity | where | finding |
|---|---|---|---|
| m1 | MINOR | U2 result `:71–72` | The revision note says "reviewed→final = **+19 lines/+1,948 B** and `c03f0cbd…`→final **+9 lines/+637 B**". Those are the totals for the **5,841-byte** R6-era object; the committed object is 76 lines/**5,845 B**, whose true totals are **+19/+1,952** and **+9/+641**, exactly as census `:126` and sidecar `:8` state (4 B stale). This is the same "copied forward from the pre-edit object" mode R6 diagnosed, now negligible and value-neutral. It cannot be corrected without changing the U2 result's sha, which sidecar `:7` binds — a correction therefore needs a fresh sidecar binding/review; carried as recorded. |
| m2 | MINOR (record/preservation) | commit `3c6ce37a`; captures | The commit is commit-reachable for **7,006 of 7,055** hashed capture entries (0 hash mismatches among those present). **49 hashed entries are gitignored by the repo `.gitignore` (`*.log`, `*.out`, `*.jsonl`, `__pycache__/*.pyc`) and are absent from HEAD**: 16 log/out files (including all nine `run.log`, e.g. `runs_smoke/s000_baseline/run.log`), `runs_smoke/smoke_ledger.jsonl`, and 32 `__pycache__/*.pyc`. A fresh checkout's `shasum -a 256 -c SHA256SUMS` would therefore report 49 missing entries (7,006 OK), whereas the delivered working-tree check is 7,055/7,055 OK. Consequence: the raw source of the cited parent peak — `AR_INFO parent_peak_vram_mb=6560.3` in `s000_baseline/run.log` — is not in git (the value itself is recorded in the committed U2 result `:36` and census `:73`, and the other cited AR values are supported by committed `facts.json`/`slowdown.json`/`sampler_max.json`/`verify_full.summary.txt`/`disk_after.txt`/pins). This is the repo-wide gitignore practice, not a delta-introduced value defect: the accepted seven U2 bundles carry the same class (41–43 hashed gitignored entries absent from HEAD, e.g. `u2_iso_mlab_cifar10…`: 428 entries, 43 absent), and the TASL-7 captures/retry dir carry 17/21. The sidecar `:11` "AR evidence/SHA256SUMS commit caveat resolved by this commit" is accurate for the R5-C10 object (the Ada AR smoke bundle is fully committed: 1,800/1,800 entries in HEAD) and for committing the TASL-2 capture tree, but it overstates **full fresh-checkout verifiability** of the new TASL-2 bundle. Record-only; no measured value, gate, isolation record or U2 status changes. Next natural revision should either force-add the 49 or state the 49-entry caveat; this acceptance does not require reopening the commit. |
| m3 | MINOR (carried from R6 C5) | census `:23/:96–97/:107/:114–115/:123`; sidecar `:10`; U2 result `:75–76` | R6 C5 (m1–m7) is only partly applied. Fixed: m1 ("R5 had 2 MAJOR (not 3)"; R6's 3 MAJOR recorded). Carried/residual, all pre-existing and value-neutral: **m2** census `:123` still says "successor of **pre-fix** `0a1fa3a4…`" and the Blocked section `:96–97` still says "the earlier Ada attempt"/"vs Ada 67.901 s" without naming the 17 Nov Ada un-isolated U2 in that sentence (named at `:65`); **m3** the record cell `:23` carries the captures sha and `7,055/7,055 OK` but not the smoke sha `8814eecc…` beside the record, and licence/availability is not to U1 §7 (openly carried in the dispositions); **m4** the census host caveat `:114–115` lacks the explicit "AR option-A gate only" and §5 item 5/§5.5 "open" wording (sidecar `:12` does carry "both option-A host gates, not §3 item-7 CUDA-IPC passes"); **m5** where the author-signed `R1-TRACKG-AR-U2-TASL2` row/delegation is preserved is still an open residual (U2 result `:75–76`), not a recorded location; **m6** census `:107` "All eight rows are complete in the census sense" weak qualifier remains; **m7** sidecar `:10` chain names objects but not accepting/rejecting review shas (seven-node R5 `9c604f1b…`, AR R2 `5fe423ac…`, R3 `4c5f1848…`, R4 `d4c3f9f0…`, AR R5 `8737edf4…`). None affects a value or the binding; carried. |
| t1 | traceability note (not a finding against a value) | — | The R6 objects (census `26a30673…` 140/15,045; sidecar `4880b3a0…` 12/2,618; U2 result `86bdd429…` 76/5,841) and the earlier R2–R5 objects (`4e050ad2…`, `76bf88db…`, `79ad29ca…`, `2dbf2c16…`, `ca3bcadd…`, `3bb015a1…`, `8430854c…`, `c03f0cbd…`, `ee21f6d9…`) are not preserved in git, so the R6→final delta is auditable only against R6's verbatim quoted sizes. That cross-check passes: +3/+222 (census), +4 B (U2 result) and +1/+58 (sidecar), and R3/R4→final deltas exceed R6's computed R3/R4→R6 deltas by exactly the census delta. The accepted revision itself is now git-preserved at `3c6ce37a`. |

**No BLOCKING was found, and no fabricated, altered or overclaimed measured value was found.** The delta closes the
R6 MAJORs, the binding pair is internally consistent and committed, and the remaining items are record-only MINORs
that are carried and do not change any measured number, pin, manifest, gate capture, isolation record or U2 status.

## 4. Acceptance binding and read-only attestation

This review is the documented **delta-only spot-check** required by R6 condition C6 and binds to commit
**`3c6ce37a94e1f95cf8f7b322115246209aee79ac`** (`origin/ops-tasl-20261116`) with: census SHA-256
**`d7f8f8aab2c4d1002c8f666caca0ae4393ca11514d3d040ac0949f1657c79890`**, 143 lines / 15,267 bytes; binding
sidecar SHA-256 **`4212e6caa9b4890d88a00498b27a685b0c1456f8b3b2464e6a1db6aecb1ef341`**, 13 lines / 2,676 bytes;
U2 result SHA-256 **`8f872f2da42ad6256ac037e5aca267be295d4063edd1ae473e74c7ae47be4d86`**, 76 lines / 5,845 bytes;
unit sibling SHA-256 **`b83d91597eaf665b942f4f02fd30f149da53f5f1cc0e6579d1e6711669734432`**, 74 lines / 6,374 bytes.
**Verdict: ACCEPTED (delta-only)** — 0 BLOCKING, 0 new MAJOR, 3 MINOR carried (m1–m3), 1 traceability note (t1).
Any further edit to the census invalidates the sidecar binding; any edit to the U2 result invalidates sidecar `:7`
and requires a fresh binding and a fresh review. Nothing in this review changes a measured number, pin, manifest,
gate capture, isolation record or U2 status.

**Written:** only this review file (untracked). **Read-only:** all cited files, captures and records; `shasum -a
256`; `shasum -a 256 -c` (7,055/7,055 OK, rc 0, working tree); `python3` JSON re-parses; table cell counts; row
byte-identity vs the parent census blob; `git rev-parse/status/log/show/ls-tree/cat-file/branch --contains`;
`wc`, `stat`, `grep`, `diff`, `sed`, `read`. **Not done:** no run, smoke, U2/GPU/T1/census job, probe,
SSH/live-host inspection, edit outside this review, commit, push, deletion/move, HTCondor/deepthought action, or
secret/credential read. No other review's object was modified.
