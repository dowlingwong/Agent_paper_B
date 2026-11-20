# Independent review (round 4) — Track G U4 census (`TRACKG_U4_CENSUS_20261120.md`) — 20/21 November 2026

**Reviewer role.** Fresh, independent, read-only fourth-round reviewer (`u4-census-reviewer-r4`), delegated
after the round-3 review returned NOT ACCEPTED (0 BLOCKING, 1 MAJOR, 9 MINOR). No involvement in the seven U2
units/results, the isolated-kit update, the isolation fix/code unit, the autoresearch option-A code unit/smoke,
the census, or the round-1/round-2/round-3 reviews. Read-only: the only file written is this review
(uncommitted/untracked). No smoke/U2/GPU/Ada/SSH run, no unit/result/record/census edit, no commit/push/delete,
no HTCondor/deepthought/TASL. The paper records, captures, review chain, local git state and the sibling
harness worktree were read only.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`35d2c3e38eba0d59047f603fe8192a828736b6d18f14dc3727a3c821d7ce8deb`**, **109 lines / 10,263 bytes**, mtime
**2026-11-20T23:05:56Z** (21 Nov 00:05:56 local), **untracked** at worktree HEAD **`92ed9bb9`** (branch
`ops-tasl-20261116`). The round-3 object (per the R3 review header: sha `39c0932a…`, 99 lines) is **not preserved**
— it is not a git object and the only census copy in the workspace is the current file — so the R3→R4 delta cannot
be audited byte-for-byte; this review recomputes every measured value from the preserved records instead (m9). The
seven-row measured table is unchanged from the values the R3 review quoted, which bounds the risk of the in-place
rewrite.

**Authority / inputs read.**
- The round-3 review `docs/r1/reviews/TRACKG_U4_CENSUS_REVIEW_R3_20261120.md` (sha **`a18c02cb…`**, 356 lines),
  round-2 review (sha `04b5893c…`, 324 lines) and round-1 review (sha `f8ffe193…`, 282 lines).
- The committed autoresearch result directory at HEAD `92ed9bb9`
  `docs/r1/reports/trackg_g0_20261117/ar_cond7a_smoke_20261120T223548Z/`, verified against the commit blobs:
  `DONE`, `RESULT_STATUS.txt`, `U2_ISO_AR_COND7A_RESULT_20261120.md` (sha **`bcb74efc…`**), `SHA256SUMS` (sha
  **`231d388e…`**), `failure_time_census.txt`, `gate/gate_20261120T223548Z.json`, `gpu/{gpu_qualify,gpu_before,
  gpu_mid,gpu_after}.txt`, `slowdown.json`, `summary.json`, `verify_full.json`, `runs/runs_smoke/s000_baseline/
  run_record.json` and `s001/run_record.json`, `pins.txt`, `prep/pins_{committed,deployed}.txt`, `cgroup_probe.txt`,
  `launch_ar_cond7a_attempt1.log`, `launch_attempt1.log`, `logs/run_node.log`, `reference/` copies; and the code
  unit/review (`TRACKG_AR_COND7A_CODE_UNIT_20261120.md`, `TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha
  `261a03e9…`).
- The seven isolated U2 result directories `u2_iso_*_2026111*Z` / `u2_iso_mlgym_houseprice_20261120T215244Z/`:
  all `run_record.json` (7 × 9 = 56 executed + 7 refused `s001`), `SHA256SUMS`, `pins.txt`, `verify_full.json`,
  `summary.json`, `time_v.txt`, `disk_before.txt`/`disk_after.txt`, `data_manifest.txt`, `gate/*.json`,
  `cgroup_probe.txt`, `smoke_stdout_extract.txt`.
- `docs/r1/PLAN.md` at HEAD `94db94bb` (`R1-TRACKG-G0-GO` `:1258`, `R1-TRACKG-LICENCES` `:1269`,
  `R1-TRACKG-PORT-DECISIONS` `:1289`, `R1-HARNESS-ISOLATION` `:1290`, `R1-TRACKG-AR-COND7` `:1317`,
  `R1-TRACKG-G3-EARLY` `:1330`; the PLAN at `de3de54f` has 1317 lines, so G3-EARLY is HEAD-only).
- `U1_LICENCE_AVAILABILITY_20261117.md` (sha `70d54b71…`) §7 / §8, `TRACKG_CENSUS_20261117.md` (sha `5cd2a0cb…`),
  `TRACKG_G0_ADA_CENSUS_20261116.md` (sha `903fc8a5…`), `TRACKG_ISO_KIT_UPDATE_20261119.md` (sha `fe232e2b…`) and
  its review (sha `d8c68f9f…`, which records it reviewed `3c3ae74a…`), `TRACKG_PORT_ISOLATION_20261117.md`
  `:98-99` (mandated imdb sentence), the unit/result reviews (`99daf16d…`, `965dc993…`, `d4cdd9bb…`, `b2c463a7…`),
  `HARNESS_ISOLATION_FIX_20261119.md` (`0ff9a7f2…`), `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (`c8e468c7…`).

---

## Verdict: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 13 MINOR (8 open from R3, 5 new)

The **M1 MAJOR is only partly closed.** The census's "Blocked / not passed" section (`:76-92`) now correctly
records that the one authorised isolated Ada smoke was **attempted on 20 Nov and STOPPED at 22:54:22Z** (external
co-tenant CUDA OOM; no retry; `CHECKLIST_E_PASSED` not reached; slowdown **not** measured), matches the committed
result dir at HEAD `92ed9bb9` on **every material fact** (§1.1), and correctly keeps `autoresearch_fixedtokens`
blocked pending a clean smoke + U2 (§1.3). **But the funnel appendix sentence at `:58-59` is unchanged from the R3
object and still asserts the isolated smoke is "pending an idle GPU"** — the exact affirmative status claim R3's
C1 required rewriting. The document still contradicts itself and the committed record on a candidate node's
status (**M1 remains open**; a one-line documentation fix). The measured seven rows are fully sound (§2): every
value recomputes exactly, all seven `SHA256SUMS` verify rc 0, and there is **no fabricated or overclaimed
number**. Of the nine R3 MINORs only **m3 is closed**; m1, m2, m4, m5, m6, m7, m8, m9 remain open (§3). Five new
MINOR residuals (n1–n5) are recorded (§4).

---

## 1. M1 closure verification against the committed record (HEAD `92ed9bb9`)

### 1.1 Census claims about the AR smoke — all verified against the committed result dir

| census claim | committed evidence | match |
|---|---|---|
| smoke **attempted 20 Nov**, launched **22:35:48Z** on card 5 `GPU-5357dc5f…`, **verified idle** | `launch_ar_cond7a_attempt1.log` start=2026-11-20T22:35:48Z; `gpu/gpu_qualify.txt` 22:35:51Z: card 5 `48427 MiB` free, `0 %`, `other_compute_apps_on_card=0`; `gpu_before.txt` 22:35:53Z 5 MiB used | ✅ |
| co-tenant **zihaozhao, 9 processes, started ~3 min later** | `failure_time_census.txt` (22:54:14Z) lists exactly 9 zihaozhao pids on card 5 (4093944/45/46, 4098825, 4098838, 4099009, 4099060, 4099068, 4099263), etimes 15:07–15:32 → started ≈22:38:42–22:39:07 (launch 22:35:48 → ≈2 min 54 s) | ✅ |
| baseline **died with CUDA out of memory** | `U2_ISO_AR_COND7A_RESULT_20261120.md` §4 (`torch.OutOfMemoryError … 157.00 MiB free`); `s000_baseline` outcome `divergent / nonzero_exit / value null`, `returncode 1`, `timed_out:false` | ✅ |
| **STOPPED at 22:54:22Z** (`DONE_STOP`, rc 137) | `DONE` = `DONE_STOP 2026-11-20T22:54:22Z`; `RESULT_STATUS.txt` `status=STOP`, `systemd_run_rc=137`, `end_utc=2026-11-20T22:54:22Z` | ✅ |
| only **baseline record + refused s001** exist | `summary.json`: exactly 2 records — `s000_baseline` (`executed:true`) and `s001` (`executed:false`); `s002` partial with no record | ✅ |
| no **`CHECKLIST_E_PASSED`** | `smoke_stdout_extract.txt` = **0 bytes**; `RESULT_STATUS.txt` `checklist_e_passed=0`, "STOP: CHECKLIST_E_PASSED autoresearch_fixedtokens missing" | ✅ |
| **transfer slowdown was not measured** | `slowdown.json`: `B2_seconds:null`, only the failed baseline `748.79 s`; report §5: that wall and the `1.057 s` surrogate are **invalid as transfer measurements** | ✅ |
| **external co-tenancy failure, not a code failure; no CUDA IPC error** | `verify_full.json` `no_cuda_ipc_error:true`; report §4 AST scan NONE; log has no CUDA-IPC marker | ✅ |
| isolation **`effective:true` / `waivers {}` / `exceptions []`**, private `/dev/shm` | `s000_baseline/run_record.json` `isolation.effective:true`, `waivers {}`, `exceptions []`, `log_intact:true`, `worker_sandbox.shared_dev_shm:false`, `cgroup.kill.empty_after:true`/`removed:true` (11 procs), result channel empty (`e3b0c44…`) | ✅ |
| training completed **500 steps, peak VRAM 1,980.1 MB** | report §4 `500/500 steps`, `AR_TOKENS consumed=32768000`, `AR_INFO peak_vram_mb=1980.1`; `slowdown.json` `peak_vram_mb_worker:1980.1` | ✅ |
| frozen pin **`147f0d35…` (committed) / `069e987a…` (deployed)** | `pins.txt`, `prep/pins_committed.txt`, `prep/pins_deployed.txt`; `run_record.frozen_pin_sha256 = 069e987a…` | ✅ |
| **one smoke consumed; no retry** | exactly one result dir and one launch attempt (`launch_ar_cond7a_attempt1.log`/`launch_attempt1.log`); `RESULT_STATUS.txt` "(timeout/OOM/failure; no retry)"; report §6.5 "No retry was performed" | ✅ |
| **isolated U2 not run; 17 Nov un-isolated U2 passed B1 67.901 s** | report §5 reference `B1 67.901 s`; `slowdown.json.reference_17nov`; accepted `TRACKG_U2_AR_RESULT_20261117.md` per prior reviews | ✅ |
| **row blocked pending clean smoke + U2** | report §6.5; `R1-TRACKG-G3-EARLY` join condition; census `:91-92`, `:97-98` | ✅ |
| **report sha `bcb74efc…`, SHA256SUMS `231d388e…`** | `shasum -a 256` of both files (working tree and HEAD blobs) **both match** | ✅ |
| gate capture `clear_finished`, paper_a_processes [] | `gate/gate_20261120T223548Z.json`: `verdict:clear_finished`, `paper_a_live_waiting_for_card:false`, `evidence.gpu.paper_a_processes:[]` | ✅ |
| card-5 co-tenant size **`~42.6 GiB`** | 3×4566 + 3×6862 + 3×2762 MiB = **42,570 MiB = 41.6 GiB** (42.6 GB decimal) — the committed report itself labels it "≈42.6 GiB"; census inherits the unit slip → **n1** | ⚠️ label |

**The Blocked-section narrative is therefore accurate and traceable to the committed record.** No claim there is
fabricated; the "no idle GPU" condition for a fresh run is correctly implied by "a fresh isolated smoke needs a
guaranteed-idle card for the whole run" (`:89-90`).

### 1.2 M1 residual — `:58-59` still says the isolated smoke is pending (MAJOR)

The census still says, unchanged from the R3 object:

> `:58-59` — "**autoresearch (1 node):** not in this census; condition-7 option-A code unit accepted, isolated
> smoke pending an idle GPU; joins after smoke+U2."

This is the same sentence R3's **C1 explicitly required rewriting**, and it is still the affirmative claim that
the smoke has not yet run. It contradicts (a) the same document's `:81-92` ("The one isolated Ada GPU smoke was
attempted on 20 Nov … the smoke was STOPPED at 22:54:22Z … transfer slowdown was not measured … One smoke was
consumed; no retry … the row joins … only after a clean smoke + U2 review") and (b) the committed record
(§1.1). A reader of the funnel appendix would conclude the one authorised smoke is still waiting for a GPU and
will still produce the measurement, when in fact it was consumed and failed externally and a new smoke needs fresh
authorisation.

Even under the charitable reading "a fresh smoke is pending a guaranteed-idle card", the sentence must be
disambiguated ("a fresh/clean smoke is pending a guaranteed-idle card"), otherwise it directly contradicts the
Blocked section. **M1 is therefore not closed**; the fix is documentation-only and needs no run.

### 1.3 No other "pending/planned" claim remains

`grep` of the census finds no "will measure", "not yet", "planned" or "await" status claim for AR; the only
"pending" is `:58-59` (and the legitimate "a fresh isolated smoke needs a guaranteed-idle card", `:89-90`). The
`isolated U2 not run` statement (`:91-92`), the 17 Nov un-isolated pass (`B1 67.901 s`), and the join condition
(`:91-92`, `:97-98`) are all correct. **The R3 C1 requirement is satisfied everywhere except `:58-59`.**

### 1.4 Committed result-dir integrity (read-only)

- `DONE`/`RESULT_STATUS.txt`/report/SHA256SUMS are committed at HEAD and their working-tree shas equal the HEAD
  blobs; `DONE_STOP 22:54:22Z`, `systemd_run_rc=137`, `checklist_e_passed=0`, `end_utc=22:54:22Z`.
- `shasum -a 256 -c SHA256SUMS` in the AR dir: **rc 0, 1,800 entries, 0 failures** (working tree).
- Gate/gpu/records/pins captures are committed and internally consistent (§1.1).
- **Caveat (n5):** the committed `SHA256SUMS` lists **1,800** files but only **1,789** are in HEAD; **17 hashed
  files are not committed** (gitignored): `logs/run_node.log`, `runs/.../s000_baseline/run.log`,
  `runs/.../s002/run.log`, `prep/setup.log`, `launch_ar_cond7a_attempt1.log`, `launch_attempt1.log`,
  `gpu_wait.log`, `cond7a_gpu_wait.log`, `smoke_ledger.jsonl`, and 8 `__pycache__/*.pyc`. A fresh checkout
  therefore cannot re-run the committed SHA256SUMS to completion; it does verify locally (all 1,800 OK). This is
  a commit-completeness/traceability caveat, not a census falsehood.

---

## 2. Measured rows — independent recomputation (all exact)

Mechanical cell counts: main table header+7 rows all **14 cells** (`:12-20`, `awk -F'|'`); run-level table
header+7 rows all **5 cells** (`:24-32`). The R2 M1 column-shift closure holds.

| node | B1 s / value | B2 s / value | sealed test | 3×B1 | max RSS kB | disk before→after (B) | committed / deployed | manifest | UUID (card) / cpus | gate |
|---|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 / 0.5152 | 11.846 / 0.5152 | 0.5015 | 36.891 | 1,402,612 | 74,632,835,072→74,630,283,264 | `1f047ad7` / `a459b3d8` | `43fdf860` | aa340032 (1) / 0-7 | clear |
| mlab_imdb | 64.142 / 0.9048 | 64.133 / 0.9048 | 0.89924 | 192.426 | 1,659,008 | 74,629,115,904→74,609,201,152 | `4b1019a6` / `c169a6b8` | `a87254e1` | f439cca8 (2) / 0-7 | clear |
| mlab_ogbn_arxiv | 5.651 / 0.275982 | 5.665 / 0.275982 | 0.238442 | 16.953 | 1,256,776 | 74,610,388,992→74,605,633,536 | `bd71fdf4` / `5ff5824a` | `91312162` | 3b36edea (6) / 0-7 | clear |
| mlgym_cifar10 | 31.731 / 0.491 | 31.244 / 0.491 | 0.4926 | 95.193 | 1,493,864 | 74,604,687,360→74,597,408,768 | `2d7e533b` / `817c9034` | `c0ef1168` | 3719bd35 (7) / 8-15 | clear |
| mlgym_fmnist | 34.376 / 0.861667 | 28.868 / 0.861667 | 0.8515 | 103.128 | 1,213,024 | 74,596,868,096→74,548,490,240 | `eb60107e` / `ef804338` | `8d28287b` | f439cca8 (2) / 8-15 | clear |
| mlgym_breakout_minatar | 61.248 / 22.486719 | 61.781 / 22.486719 | 22.885938 (`test_return`) | 183.744 | 1,262,488 | 75,439,427,584→75,401,625,600 | `cec562e6` / `cec562e6` | none (simulated) | 3b36edea (6) / 8-15 | clear |
| mlgym_houseprice | 5.059 / 23344.767385 | 4.876 / 23344.767385 | 30295.671017 (`test_rmse`) | 15.177 | 599,392 | 70,644,187,136→70,795,374,592 | `88d359f2` / `4cbbc5d6` | `73ee5597` | CPU 79,78,77,76,59,42,34,28 | clear |

- Every B1/B2 elapsed and `outcome.value` equals the `s000_baseline`/`B2` `run_record.json`; every sealed value
  equals `run_record.sealed.<key>`; `3×B1` equals 3 × B1 exactly; max RSS equals each `time_v.txt` "Maximum
  resident set size (kbytes)"; disks equal the `/dev/md0p3` Available bytes in `disk_before/after.txt`; committed
  pins match `pins.txt`, deployed pins match the executed records; manifests match `data_manifest.txt`; UUIDs and
  cpusets match `limits.gpu_uuids`/`limits.cpu_list` (the census's "cpus 0-7"/"8-15" is shorthand for the record's
  `[0…7]`/`[8…15]`); every gate JSON is `clear_finished`, `paper_a_live_waiting_for_card:false`, `paper_a_processes
  []`; every `smoke_stdout_extract.txt` carries `CHECKLIST_E_PASSED`; every dir has 9 records = 8 executed + 1
  refused `s001`.
- `shasum -a 256 -c SHA256SUMS` **rc 0 in all seven dirs** (428 / 427 / 426 / 426 / 426 / 1,117 / 447 entries OK,
  0 failures).
- Exactly the seven `u2_iso_*` dirs referenced by the census exist; the census references exactly those seven.
  **No fabricated row, no overclaimed number.**

---

## 3. R3 MINOR closure matrix

| round-3 item | status | evidence in the current object |
|---|---|---|
| m1 metric-key labelling | **open** | `:14-18` name `val_accuracy` in B1 and B2, but the **sealed-test cells of the five accuracy rows are still bare** (0.5015 / 0.89924 / 0.238442 / 0.4926 / 0.8515, no `test_accuracy`); B2 cells for Breakout/HousePrice still bare (22.486719 / 23344.767385, no `val_return`/`val_rmse`). R3 C2 not met. |
| m2 HousePrice bound cell + disk units/wording | **open** | `:20` still `n/a (CPU)` with the 599,392 kB only in the run-level table (`:32`); no RAM/VRAM label or cross-reference; disk cells (`:26-32`) still have no `B` unit; `:34-36` still says "disk before/after … are in the record captures" although the table now carries them. |
| m3 "U2 not run" opener | **closed** | `:76-77` now opens "isolation condition 7 … failed on Ada pre-fix"; the precise "isolated U2 is **not run** (17 Nov un-isolated passed B1 67.901 s)" is at `:91-92`. |
| m4 fix-review verdict + duplicate filename | **open** | `:67-69`: sha `c8e468c7…` is present but the **`ACCEPTED` verdict is missing**, and `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` is still listed **twice** (`:68` duplicate without sha). |
| m5 per-node licence/availability | **open** | `:43-47` and `:55-57` remain per-suite prose; `U1_LICENCE_AVAILABILITY_20261117.md` §7 supplies the per-node code+asset licence/availability table and §8 says it "supplies the U4 census's licence/availability columns" — not carried. R3 C6 not met. |
| m6 citations/shas | **open** | `:103-108`: plan rows carry revisions/lines, but **acceptances are names only with no shas**; no per-node unit reviews (`99daf16d…` etc.), no U4 basis docs (`TRACKG_G0_ADA_CENSUS_20261116.md` `903fc8a5…`, `TRACKG_CENSUS_20261117.md` `5cd2a0cb…`), no U1 audit (`70d54b71…`); "**six** isolated U2 result reviews" still names only **two** files; `R1-TRACKG-G3-EARLY (:1330)` not attributed to `94db94bb`; the kit-update report's **current sha `fe232e2b…` vs reviewed `3c3ae74a…`** (plus C-K1–C-K4) is not stated. R3 C7 not met. |
| m7 imdb verbatim disclosure | **open** | `:51-54` still paraphrases and closes with the self-referential "the census/paper appendix must carry this disclosure"; the mandated sentence (`TRACKG_PORT_ISOLATION_20261117.md:98-99`: "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton for this task.") is **not reproduced verbatim**. R3 C8 not met. |
| m8 CPU/RAM wording | **open** | `:41` still says "whole-smoke CPU/RAM aggregates labelled"; the census carries whole-smoke **max RSS** only — no whole-smoke **CPU** aggregate. R3 C9 (part) not met. |
| m9 traceability / preserve reviewed sha | **open** | The census is still **untracked** and was rewritten **in place** again (`39c0932a…` → `35d2c3e3…` at 23:05:56Z, 34 s after the R3 review file's mtime 23:05:22Z); the R3 object is not a git object and exists nowhere else. Acceptance must bind to `35d2c3e3…` and that revision must be committed/preserved. |

---

## 4. Findings

### M1 — MAJOR (remaining): the funnel appendix still states the isolated smoke is "pending an idle GPU"

`:58-59`, reproduced verbatim in §1.2, is unchanged from the R3 object and is exactly the status statement R3's
C1 required rewriting. The Blocked section (`:81-92`) and the committed record (§1.1) say the opposite: the one
authorised smoke was attempted and STOPPED at 22:54:22Z (external co-tenant OOM), no retry, slowdown not measured.
Until `:58-59` is reworded the census remains internally contradictory on a node's status, so M1 is not closed.
Docs-only fix; no run required.

### m1 — MINOR: metric-key labelling still incomplete

`:14-18` sealed cells of the five accuracy rows are still bare (`0.5015`, `0.89924`, `0.238442`, `0.4926`,
`0.8515`) with no `test_accuracy`; `:19-20` B2 cells are bare (`22.486719`, `23344.767385`) with no
`val_return`/`val_rmse`. Values are correct (verified); this is a labelling residual (R3 C2).

### m2 — MINOR: HousePrice bound cell, disk units, stale disk wording

`:20` "whole-smoke upper bound" = `n/a (CPU)`; the 599,392 kB RAM bound is only at `:32`; the column header (`:12`)
does not say VRAM. Disk cells (`:26-32`) carry byte values with no `B`; `:34-36` still says disk before/after are
"in the record captures" although the table carries them (R3 C3).

### m4 — MINOR: fix-review verdict missing and filename duplicated

`:67-69`: cite `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` **with ACCEPTED** and remove the
duplicated filename at `:68` (R3 C5).

### m5 — MINOR: licence/availability still per-suite, not per-node

`:43-47` / `:55-57` compress to per-suite prose. `U1_LICENCE_AVAILABILITY_20261117.md` §7 gives the per-node
table (MLAgentBench MIT code; MLGym CC-BY-NC-4.0; CIFAR-10 unknown; IMDb `license: other`; ogbn-arxiv ODC-BY;
Fashion-MNIST MIT; gymnax Apache-2.0; Kaggle terms) and §8 explicitly says it supplies the U4 census columns.
Add the per-node licence/availability columns (R3 C6).

### m6 — MINOR: authority/acceptance citations are names-only and incomplete

`:103-108`: add shas and complete the citations — kit-update report `fe232e2b…` **and reviewed `3c3ae74a…` plus
C-K1–C-K4** (review `d8c68f9f…`), the per-node unit reviews (incl. `99daf16d…`), the three result reviews
(`965dc993…`, `d4cdd9bb…`, `b2c463a7…`), the U4 basis docs (`903fc8a5…`, `5cd2a0cb…`), the U1 audit
(`70d54b71…`), and attribute `R1-TRACKG-G3-EARLY` to `94db94bb` (or the worktree). Correct the "**six** isolated
U2 result reviews" phrase (it lists two; the actual result reviews are three). (R3 C7.)

### m7 — MINOR: imdb disclosure not the mandated verbatim sentence

`:51-54` carries the substance but not the mandated sentence, and the trailing "the census/paper appendix must
carry this disclosure" reads as an open obligation inside the appendix. Use the verbatim sentence at
`TRACKG_PORT_ISOLATION_20261117.md:98-99` in the census appendix (and paper appendix) and drop the
self-referential clause (R3 C8).

### m8 — MINOR: "whole-smoke CPU/RAM aggregates labelled" overstates the content

`:41`. The run-level table carries max RSS only; `time -v` user/system/wall numbers are in the result mds, not the
census. Either carry the CPU-time aggregate or reword to "whole-smoke RAM (max RSS) and VRAM upper bounds
labelled" (R3 C9, part).

### m9 — MINOR (traceability): the R3-reviewed revision is not preserved

The census is untracked; it was rewritten in place from the R3 object (`39c0932a…`) to the current
`35d2c3e3…`; the R3 object is not a git object and exists nowhere else in the workspace. The measured table is
unchanged, which limits the risk, but acceptance should bind to `35d2c3e3…` and that revision must be
committed/preserved; any further revision needs a fresh review (or a preserved copy + delta) rather than another
in-place rewrite.

### n1 — MINOR: co-tenant size unit slip

`:82` "~42.6 GiB" for 3×4566 + 3×6862 + 3×2762 MiB = **42,570 MiB = 41.6 GiB** (≈42.6 GB decimal). The committed
report carries the same label, so this is an inherited slip; write "~42.6 GB" or "~41.6 GiB" (and optionally
correct the report in a separate correction note).

### n2 — MINOR: malformed result-record path

`:85-86` "Result record `u2_iso_...`/`ar_cond7a_smoke_20261120T223548Z/`" — there is no `u2_iso_...` directory
under the census's base path; the directory is `ar_cond7a_smoke_20261120T223548Z/` (the `u2_iso_20261119` prefix
exists only on the Ada evidence host). Write the repo-relative path.

### n3 — MINOR: header parenthetical reads stale for HousePrice

`:3-6` says "the six passed isolated nodes are set now for G.1b/G.4; autoresearch and HousePrice join as their U2
passes". HousePrice's U2 has passed and the census's own Readiness says "HousePrice joins now" (`:97`), so as a
current-status sentence the parenthetical is stale (it quotes the 20 Nov decision). Reword to "HousePrice joins
now; autoresearch joins as soon as its smoke + U2 pass".

### n4 — MINOR: "no retry is authorized by this census" phrasing

`:89-90`. The verified facts are: one smoke was consumed and **no retry was performed**; a new isolated smoke
needs **fresh coordinator authorisation** and a card guaranteed idle for the whole run (committed report §6.5).
The census's wording inverts this and omits the fresh-authorisation requirement. Reword.

### n5 — MINOR (commit integrity): committed SHA256SUMS does not correspond to the committed file set

See §1.4: 1,800 hashed entries vs 1,789 files in HEAD; 17 hashed files (logs, launch logs, run logs,
`smoke_ledger.jsonl`, `__pycache__`) are not committed, so the committed record cannot be fully re-verified from
HEAD alone (it verifies locally, 1,800/1,800, rc 0). Either commit the referenced evidence files or state in the
census that SHA256SUMS covers non-committed logs.

---

## 5. Conditions for acceptance (documentation only — no new run, no record/measurement edit)

- **C1 (closes M1).** Reword `:58-59` so the funnel appendix states the truth: the one authorised isolated Ada
  smoke was launched 22:35:48Z and **STOPPED at 22:54:22Z** (external co-tenant CUDA OOM; no retry;
  `CHECKLIST_E_PASSED` not reached; slowdown **not measured**); a **fresh/clean** isolated smoke needs fresh
  coordinator authorisation and a guaranteed-idle card for the whole run; joins only after a clean smoke + U2
  review. Keep the (accurate) Blocked section, including pushed branch `@7330338`, reviewed `13786d1f`, code
  review `261a03e9…` ACCEPTED (0 BLOCKING, 1 report-only MAJOR, 6 MINOR, C1–C6), report `370782ab…`, 17 Nov
  un-isolated U2 pass (B1 67.901 s), "isolated U2 not run", and the result dir `ar_cond7a_smoke_20261120T223548Z/`
  with report sha `bcb74efc…` / SHA256SUMS `231d388e…`.
- **C2 (m1).** Name `test_accuracy` in the sealed cells of the five accuracy rows and `val_return` / `val_rmse`
  in the B2 cells of Breakout/HousePrice.
- **C3 (m2).** Put (or cross-reference from) the 599,392 kB RAM bound in the `mlgym_houseprice` whole-smoke bound
  cell with an explicit RAM/VRAM label; add `B` to the disk values; fix the `:34-36` "in the record captures"
  wording.
- **C4 (m4).** Cite `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` with **ACCEPTED** (condition 6
  PASS / condition 7 BLOCKED) and remove the duplicate filename.
- **C5 (m5).** Add the per-node licence/availability columns per `U1_LICENCE_AVAILABILITY_20261117.md` §7 with the
  availability status.
- **C6 (m6).** Give shas and complete the citations as listed in m6, including the kit report's reviewed-vs-current
  sha, the per-node unit reviews, the result reviews, the U4 basis docs and the U1 audit; fix "six isolated U2
  result reviews"; attribute G3-EARLY to `94db94bb`.
- **C7 (m7).** Use the mandated verbatim imdb sentence and drop the self-referential clause.
- **C8 (m8).** Reconcile the "whole-smoke CPU/RAM aggregates" wording with what is carried.
- **C9 (m9).** Bind acceptance to the reviewed sha `35d2c3e3…` and commit/preserve that revision; do not revise in
  place again after acceptance without a fresh review.
- **C10 (n1–n5).** Fix the co-tenant unit (`~42.6 GB` / `~41.6 GiB`), the malformed record path, the stale
  HousePrice header clause, the "no retry is authorized by this census" phrasing (→ "no retry was performed; a
  fresh smoke needs fresh coordinator authorisation"), and either commit the SHA256SUMS-referenced evidence files
  or state the commit caveat.

After C1–C10 a fresh reviewer should re-check. This review authorises no run, no record edit, no commit/push, no
census launch, no T1/G.1b/G.4 action. Nothing in this review changes a measured number, pin, manifest, gate
capture or isolation record; the seven rows remain fully supported by the accepted records.

---

## 6. Acceptance binding / traceability

Acceptance is to be bound to the exact reviewed revision
**`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
`35d2c3e38eba0d59047f603fe8192a828736b6d18f14dc3727a3c821d7ce8deb`, 109 lines / 10,263 bytes,
mtime 2026-11-20T23:05:56Z**, which is currently **untracked at HEAD `92ed9bb9`**. That revision must be committed
(or otherwise preserved with its sha recorded) as part of acceptance. A further in-place revision would need a
fresh review or a preserved copy + auditable delta, because the R3 object (`39c0932a…`) was not preserved and the
R3→R4 delta could only be checked by recomputation, not byte-for-byte.

---

## 7. Attestation

Read-only review. The only file written is this review (uncommitted/untracked); no smoke/U2/GPU/Ada/SSH/
HTCondor/deepthought/TASL action; no unit, result, capture, record, pin, manifest, gate, census or review was
edited; no commit/push/delete. Commands used (all read-only, 20/21 November 2026, Europe/Berlin): `shasum -a 256`
of the census, the AR smoke report/`SHA256SUMS`/`DONE`/`RESULT_STATUS` and the review chain; `git rev-parse/show/
log/ls-tree/cat-file/status`; `stat`, `wc`, `ls`, `find`, `grep`, `awk`, `sed`; Python `json` reads of the AR
`run_record.json` (s000/s001), gate/gpu/failure-time-census/slowdown/summary/verify_full/pins/prep captures, and
of all 63 U2 `run_record.json` (56 executed + 7 refused `s001`), the seven `pins.txt`, `data_manifest.txt`,
`time_v.txt`, `disk_before/after.txt` and gate JSONs; a mechanical markdown cell count of both census tables
(14 cells × 9 rows; 5 cells × 9 rows); independent recomputation of every B1/B2 elapsed and value, sealed value,
3×B1, max RSS, disk before/after, pins, manifest, gate and UUID/cpuset for all seven rows; and
`shasum -a 256 -c SHA256SUMS` in the AR dir (1,800/1,800 OK) and in all seven U2 dirs (rc 0, 0 failures). No
live-host state is claimed beyond what the preserved records and captures and local git state contain.
