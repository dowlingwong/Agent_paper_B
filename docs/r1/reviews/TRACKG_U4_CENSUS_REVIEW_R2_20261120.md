# Independent re-review (round 2) — Track G U4 census (`TRACKG_U4_CENSUS_20261120.md`) — 20 November 2026

**Reviewer role.** Fresh, independent, read-only re-reviewer (`u4-census-reviewer-r2`), delegated after the
round-1 review returned NOT ACCEPTED; no involvement in the seven U2 units/results, the kit update, the
isolation fix, the autoresearch option-A code unit, the census or the round-1 review. Read-only: the only
file written is this review (uncommitted/untracked). No smoke/U2/GPU run, no record/unit/census edit, no
commit/push/delete, no HTCondor/deepthought/TASL. No Ada SSH was used; this is a paper re-review of the
preserved records, captures, review chain and local git state in this worktree and the sibling autoresearch
worktree (read only).

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`f6c226b7baa2d9116e6a81ddf82b60ad9e3b1824d86f73ec388816c440d893ea`**, **101 lines**, uncommitted/untracked at
worktree HEAD `30cadb81` (branch `ops-tasl-20261116`). Round-1 object was sha `7774a465…` (56 lines);
round-1 review `docs/r1/reviews/TRACKG_U4_CENSUS_REVIEW_20261120.md` (282 lines; B1 at `:140-159`, M1 at
`:161-183`, m1–m9 at `:185-232`, C1–C6 at `:235-261`).

**Authority / inputs read.**
- PLAN rows at the worktree: `R1-TRACKG-G0-GO` (`:1258`; U4 = "census 报告与各 suite 筛选漏斗"), `R1-TRACKG-LICENCES`
  (`:1269`), `R1-TRACKG-PORT-DECISIONS` (`:1289`), `R1-HARNESS-ISOLATION` (`:1290`), `R1-TRACKG-G3-EARLY` (`:1330`);
  first four rows verified at `de3de54f` (`git show de3de54f:docs/r1/PLAN.md`), `R1-TRACKG-G3-EARLY` verified at
  `94db94bb` and at the worktree, `R1-BX-D12` (`:756`).
- G.0 U4 basis `docs/r1/reports/TRACKG_G0_ADA_CENSUS_20261116.md` §2/§5 (`:31-33`, `:80-83`); T1 candidate working
  list §3 ≈8 nodes (`:40-46`); U1 `docs/r1/reports/trackg_g0_20261117/U1_LICENCE_AVAILABILITY_20261117.md`
  §7/§8 (`:239`, `:264-266`).
- The seven result directories `u2_iso_{mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,
  mlgym_breakout_minatar,mlgym_houseprice}_2026*Z/`: result mds, `SHA256SUMS`, all 63 `run_record.json` files
  (7×9; 56 executed + 7 refused `s001`), `pins.txt`, `verify_full.summary.txt`, `gate/*.json`,
  `cgroup_probe.txt`, `data_manifest.txt`/`prep/manifest.txt`, `disk_before/after.txt`, `time_v.txt`, `gpu/*`,
  `attempt1_prelaunch_*` dirs, `DONE`/`RESULT_STATUS.txt`.
- Accepted reviews/corrections: `TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (sha `965dc993…`; §8 at `:500-509`,
  both-pin table `:134`), `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` (`d4cdd9bb…`),
  `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` (`b2c463a7…`; ACCEPTED conditional C1–C7),
  `TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md` (`81580eec…`), `TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`
  (`d8c68f9f…`, ACCEPTED), `HARNESS_ISOLATION_FIX_20261119.md` (`0ff9a7f2…`; `:3-4`) and
  `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (`c8e468c7…`; `:8-10`), `HARNESS_ISOLATION_HOST_CHECK_20261119.md`
  (`6a700509…`; pre-fix STOP), `U2_ISO_RECORD_CORRECTIONS_20261119.md`,
  `U2_ISO_HOUSEPRICE_RECORD_CORRECTIONS_20261120.md`.
- Autoresearch option-A: code review `docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md`
  (sha `261a03e9…`; reviewed HEAD `13786d1f`; verdict `:18`; C1–C6 `:331-360`); code-unit report at the sibling
  worktree `.claude-worktrees/harness_ar_cond7_20261120/docs/r1/reports/trackg_g0_20261117/
  TRACKG_AR_COND7A_CODE_UNIT_20261120.md` — reviewed revision (`13786d1f`) sha `4f1f4fe0…` (238 lines), fixed tip
  (`7330338`) sha `370782ab…` (336 lines); local repo state of branch `mac-trackg-iso-ar-cond7a-20261120`,
  including `refs/remotes/origin/…` reflog; cond7a smoke staging dir
  `docs/r1/reports/trackg_g0_20261117/ar_cond7a_smoke_20261120T223548Z/` (untracked, read only).

---

## Verdict: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 8 MINOR

The round-1 **BLOCKING B1 is closed**: the revised census now has a "Census funnel and per-suite appendix"
section (`:49-61`) that states the `mlab_imdb` baseline was written by us (DistilBERT fine-tuning; MLAgentBench
skeleton), frozen/reviewed/disclosed as ours, lists MLAgentBench 3 / MLGym 4 / autoresearch 1, says no node was
dropped, and discloses both attempt-1 pre-launch refusals. The round-1 **MAJOR M1 is NOT closed**: the
`mlgym_houseprice` row (`:20`) still has **13 cells against the 14-cell header** (`:12-13`), so the committed
pin, manifest and record columns remain shifted one cell left and the RAM bound never reaches the row; the
requested disk before/after values and GPU UUID/cpuset fields are also still not carried. The seven measured
rows themselves remain **fully supported by the preserved records** (every B1/B2 elapsed/value, sealed metric,
3×B1 timeout, max RSS, VRAM bound, both pins, manifest, gate capture and UUID/cpuset matches — §1.4); no
fabricated row, no overclaimed number, and the ENGINEERING_ONLY / no-evidence / readiness labels are correct.
MINORs m1–m8 below remain and are mandatory conditions.

---

## 1. Closure verification

### 1.1 B1 (funnel / appendix) — **CLOSED**

- The census now carries a funnel/appendix section (`TRACKG_U4_CENSUS_20261120.md:49-61`). It names the three
  suites with the required counts: **MLAgentBench (3 nodes)** `:51-54`, **MLGym (4 nodes)** `:55-57`,
  **autoresearch (1 node)** `:58-59` — 3+4+1 = the ≈8 T1 working-list candidates
  (`TRACKG_G0_ADA_CENSUS_20261116.md:40-46`), matching the seven passed rows + the blocked autoresearch node.
- **mlab_imdb disclosure present** (`:51-54`): "The `mlab_imdb` baseline was **written by us** (the kit
  fine-tunes DistilBERT-base-uncased; MLAgentBench ships only a skeleton and no upstream baseline), frozen,
  reviewed and disclosed as ours; the census/paper appendix must carry this disclosure." This satisfies
  `R1-TRACKG-PORT-DECISIONS` (3) (`PLAN:1289`: note in the census funnel and appendix "baseline 由我们编写") and
  the record-chain requirement (`U2_ISO_MLAB_IMDB_RESULT_20261119.md:51-53`;
  `unit/U2_ISO_MLAB_IMDB_UNIT_20261119.md:28`; `TRACKG_PORT_ISOLATION_20261117.md:91-99`;
  `runs/runs_smoke/s000_baseline/work/LICENCES.md` "Baseline written by us"). "frozen / reviewed / disclosed" is
  supported by the `BASELINE_SHA256 01dcb7c4…` freeze, the port-kit review and the disclosure line.
- **No node dropped** (`:60`), and **attempt-1 pre-launch refusals disclosed** (`:60-61`): HousePrice CPU-idle
  STOP and Breakout gate STOP — both preserved (`attempt1_prelaunch_cpu_idle_stop/` "mean idle 70.6 % < 80 %; no
  smoke launched"; `attempt1_prelaunch_gate_stop/` gate `verdict: unknown`;
  `U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md:145-148`; `U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md:173-176`).
- **Licence/provenance per suite** is present (`:43-47`, `:55-57`): MLGym CC BY-NC 4.0 with notice, gymnax-blines
  Apache-2.0 parts used only by Breakout, HousePrice author Kaggle `train.csv` sha256
  `1e18addf…`/md5 `80ccab65…` with `--from-file` and no MLGym copy. All values re-verified in the records
  (`U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md:68,322-327`; `verify_full.summary.txt` `ar_data_line`; breakout
  `:120-123`). Caveats that keep this B1-closed only in substance are reported as m7/m8.

### 1.2 M1 (U4 row fields) — **NOT CLOSED (1 MAJOR remains)**

Verified as **closed** parts of M1/C2: whole-smoke **max RSS for all seven** is now tabulated
(`:24-32`) and each value matches the corresponding `time_v.txt` exactly (§1.4); the **deployed run-record pin
is separate** from the committed-file pin (`:24-32`, `:34-36`) and both families match the records (§1.4); each
row carries a **gate capture path** (`:26-32`) and the gate JSONs are `clear_finished`,
`paper_a_live_waiting_for_card: false`, `evidence.gpu.paper_a_processes: []`, with a UTC stamp; the base path is
stated (`:22`, `:100-101`); the
metric keys `val_accuracy`, `val_return`, `val_rmse` are named (plus `test_return`/`test_rmse`); units are
present (s, MiB, kB, B).

**Still open:**
1. **The `mlgym_houseprice` row has 13 cells against the 14-cell header** (`:20` vs `:12-13`). Counting the raw
   line (`awk -F'|'` = 15 fields incl. edges vs 16 for the header) confirms one missing cell: after
   `timeout = 15.177 s`, `n/a (CPU, 8 cpus)` occupies the *whole-smoke upper bound* column, so the committed
   pin `88d359f2…` lands under *GPU/cpus*, the manifest `73ee5597…` under *committed pin*, and the record path
   under *data manifest* — the record column is empty. The 599,392 kB RAM bound is not in the row. This is
   exactly the defect round-1 M1 (`:161-183`) and C2 (`:245-247`) required to be fixed ("fix the HousePrice row
   to 14 cells with the RAM bound value (599,392 kB) in the bound column; label VRAM vs RAM").
2. **Disk before/after is not carried per row.** The `disk before/after` column (`:26-32`) gives actual values
   only for HousePrice (`/dev/md0p3` free 70,644,187,136 → 70,795,374,592 B — matches `disk_before.txt`/
   `disk_after.txt`); the other six rows say "in that record's … captures"/"same". The accepted five-node review
   §8 (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md:500-509`) requires the census row to supply "disk free
   before/after"; a pointer is not the row field (C2).
3. **GPU UUID + cpuset still absent.** The `GPU/cpus` column (`:14-20`) gives only the local card index
   (`card 1/2/6/7/2/6`) and `n/a (CPU, 8 cpus)`. The records carry, and the census omits, the stable UUIDs
   (`GPU-aa340032…`=card 1, `GPU-f439cca8…`=card 2, `GPU-3b36edea…`=card 6, `GPU-3719bd35…`=card 7; verified
   against each `gpu/gpu_before.txt` index table) and the cpusets (`0-7` for the three mlab nodes, `8-15` for
   the three GPU mlgym nodes, `79,78,77,76,59,42,34,28` for HousePrice; `limits.cpu_list`). This is the
   round-1 m2 residual and C3 item (`:248-250`).

### 1.3 MINOR closures (round-1 m1–m9); §2 renumbers the surviving items m1–m8

Mapping for §2: m1←round-1 m1, m2←m2, m3←m3, m4←m4, m5←m5, m6←m7, m7←m8; §2 m8 (imdb verbatim wording) is a
closure caveat of B1 rather than a round-1 item; round-1 m6 and m9 are closed.

| round-1 item | status | evidence |
|---|---|---|
| m1 metric-key naming | **partial** | `val_accuracy` now named in the B1-metric cell for five rows (`:14-18`); the B2-metric cells for those five are still bare numbers, and the five sealed cells write bare `0.5015/0.89924/…` without `test_accuracy` (Breakout/HousePrice do name `test_return`/`test_rmse`). B1 item ✓, B2/sealed labels not. |
| m2 GPU/cpus units/IDs | **not closed** | see §1.2 item 3 (card index only; no UUID, no cpuset; VRAM-vs-RAM unit now labelled in prose at `:41-43`, and MiB/kB in tables). |
| m3 autoresearch bullet | **mostly closed, one defect** | review ACCEPTED with 1 report-only MAJOR + 6 MINOR/C1–C6 `:78-80`; reviewed `13786d1f` ✓; report fix `7330338` ✓; 17 Nov un-isolated U2 passed / isolated U2 not run `:82-84` ✓. But "branch local-only and unpushed at the time of this census" `:80-81` is **stale**: the branch is on `origin/mac-trackg-iso-ar-cond7a-20261120` @ `7330338` (reflog "update by push", 2026-11-20T22:28:36Z; the cond7a smoke prep fetched it from origin at 22:31:17Z), whereas the census's last write is 22:46:10Z. The code-unit report is cited by bare filename with no sha (`:81`) and does not resolve in this worktree. |
| m4 "U2 not run" | **partial** | `:77` still opens with "U2 not run"; the precise statement ("the **isolated** autoresearch U2 is not run", with the 17 Nov un-isolated U2 passing at 67.901 s) is present at `:83-84` (`TRACKG_U2_AR_RESULT_20261117.md:3,44`). |
| m5 condition 6/7 | **partial** | `:67-69` cites the fix report with sha `0ff9a7f2…` and the pre-fix host check as superseded ✓. But the fix review is cited without its sha `c8e468c7…`/ACCEPTED verdict; the fix report `:3-4` and review `:8-10` do say condition 6 PASS / condition 7 BLOCKED. |
| m6 attempt-1 refusals | **closed** | `:60-61` discloses both pre-launch STOPs; they are preserved and described in the records. |
| m7 licence/availability columns | **partial** | per-suite licence prose exists (`:43-47`, `:55-57`), but not per-node licence/availability columns as U1 §7-8 (`U1_LICENCE_AVAILABILITY_20261117.md:239,264-266`) supplies them; no availability status column; MLAgentBench code licence (MIT verified) and the CIFAR-10/IMDb/OG-B arXiv per-item statements are compressed into one "generic citation" sentence. |
| m8 authority/acceptance citations | **partial** | `:93-101` now names the plan rows, kit-update report/review, result reviews and HousePrice unit/result reviews, isolation fix review ✓ — but all by bare filename, with no shas; per-node unit reviews (e.g. `TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md`) and the U4 basis docs (`TRACKG_G0_ADA_CENSUS_20261116.md`, `TRACKG_CENSUS_20261117.md`, the U1 audit) are still not cited. The phrase "six isolated U2 result reviews" (`:97`) but names two files (5-node + Breakout) is loose. |
| m9 relative paths | **closed** | base path `docs/r1/reports/trackg_g0_20261117/` stated at `:22` and `:100-101`; all seven record paths resolve (verified). |

### 1.4 Independent recomputation of the seven rows (all values verified from the result dirs)

Compared each census cell against `run_record.json` (`outcome`, `elapsed_seconds_info_only`, `sealed`,
`limits`), each result md's B1/B2 table, `time_v.txt`, `pins.txt`, each gate JSON, the data manifests and the
per-node captures. **Every value matches; no fabricated row and no overclaim.**

| node | B1 s / value | B2 s / value | sealed | census 3×B1 | recomputed 3×B1 | max RSS kB | VRAM bound MiB | committed / deployed pin | gate | card / cpuset |
|---|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 / 0.5152 | 11.846 / 0.5152 | 0.5015 | 36.891 | 36.891 | 1,402,612 | 836 | `1f047ad7…` / `a459b3d8…` | `clear_finished` | 1 / 0-7 |
| mlab_imdb | 64.142 / 0.9048 | 64.133 / 0.9048 | 0.89924 | 192.426 | 192.426 | 1,659,008 | 11,292 | `4b1019a6…` / `c169a6b8…` | `clear_finished` | 2 / 0-7 |
| mlab_ogbn_arxiv | 5.651 / 0.275982 | 5.665 / 0.275982 | 0.238442 | 16.953 | 16.953 | 1,256,776 | 4,544 | `bd71fdf4…` / `5ff5824a…` | `clear_finished` | 6 / 0-7 |
| mlgym_cifar10 | 31.731 / 0.491 | 31.244 / 0.491 | 0.4926 | 95.193 | 95.193 | 1,493,864 | 982 | `2d7e533b…` / `817c9034…` | `clear_finished` | 7 / 8-15 |
| mlgym_fmnist | 34.376 / 0.861667 | 28.868 / 0.861667 | 0.8515 | 103.128 | 103.128 | 1,213,024 | 912 | `eb60107e…` / `ef804338…` | `clear_finished` | 2 / 8-15 |
| mlgym_breakout_minatar | 61.248 / 22.486719 | 61.781 / 22.486719 | 22.885938 | 183.744 | 183.744 | 1,262,488 | 634 | `cec562e6…` / `cec562e6…` (equal) | `clear_finished` | 6 / 8-15 |
| mlgym_houseprice | 5.059 / 23344.767385 | 4.876 / 23344.767385 | 30295.671017 | 15.177 | 15.177 | 599,392 | n/a (CPU) | `88d359f2…` / `4cbbc5d6…` | `clear_finished` | CPU / 79,78,77,76,59,42,34,28 |

- Every row's `3×B1` equals the census timeout exactly (`limits.provisional_timeout_seconds: 1800.0`,
  `timeout_factor: 3.0` for the provisional measuring run; 3×B1 for the census value) — verified for all seven.
- Max RSS values are the `time_v.txt` "Maximum resident set size (kbytes)" values (1,402,612 / 1,659,008 /
  1,256,776 / 1,493,864 / 1,213,024 / 1,262,488 / 599,392) and match the result mds (`…CIFAR10_RESULT:160-161`,
  `…IMDB_RESULT:147`, `…OGBN_ARXIV_RESULT:149`, `…MLGYM_CIFAR10_RESULT:148`, `…FMNIST_RESULT:148`,
  `…BREAKOUT_RESULT:228`, `…HOUSEPRICE_RESULT:240-241`).
- VRAM bounds are the labelled whole-smoke upper bounds (`…CIFAR10_RESULT:124-125`, `…IMDB_RESULT:110-112`,
  `…OGBN_ARXIV_RESULT:112-114`, `…MLGYM_CIFAR10_RESULT:111-113`, `…FMNIST_RESULT:111-113`,
  `…BREAKOUT_RESULT:181-182`); HousePrice is CPU-only (`gpu_uuids: []`).
- Each dir has exactly **9 `run_record.json` = 8 executed + refused `s001`** (`executed:false`,
  `scope_violation`); every executed record has `isolation.effective:true`, `waivers {}`, `exceptions []`,
  `log_intact`, result-channel sha, `cgroup.kill.empty_after:true`, `process.timed_out:false`; every
  `cgroup_probe.txt` shows inside-scope `memory.max=8589934592`, `memory.swap.max=0`; `DONE`/`RESULT_STATUS` and
  `smoke_stdout_extract.txt` carry `CHECKLIST_E_PASSED` (the cifar10/breakout/HousePrice first `STOP` lines are
  the preserved v1-verifier false negatives, re-verified `DONE_PASS_CORRECTED`).
- Data manifests: six nodes point outside the repository and contain no `synthetic` marker; Breakout is
  simulated with no manifest (`data_manifest.txt` "data=none: … simulated environment"); HousePrice manifest has
  `synthetic` absent and `data_outside_repo=yes`.
- No fabricated/extra row: the census references exactly the seven `u2_iso_*` directories present (all seven
  resolve).

### 1.5 Readiness / labels / authority

- **G3-EARLY** (`PLAN:1330`): "the six earlier passed nodes are set for G.1b/G.4; HousePrice joins now;
  autoresearch joins when its option-A smoke + U2 pass" (`:89-90`) is correct — the six are exactly the G3-EARLY
  six; HousePrice's result review is ACCEPTED (`b2c463a7…`) with corrections applied (result md sha
  `0b1212e3…`, `SHA256SUMS` `7607fc5c…` verified), so it joins now; the census does not block G.1b/G.4.
- **ENGINEERING_ONLY / not evidence / no noise floor / no D21 / no D28 / no T1 label** (`:3-8`, `:43`, `:90`)
  matches `R1-TRACKG-G0-GO` ("G.0 不出任何噪声底或 D21 结论") and every result/unit. No HTCondor/deepthought claim.
- **Kit tips/fix** verified: `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` and
  `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf`, both containing the accepted
  isolation core fix `5403392e` (verified `git merge-base --is-ancestor`), exactly as printed at `:65-66`.
- **Authority rows** verified at the cited revisions/lines: `de3de54f` `:1258/:1269/:1289/:1290`; `94db94bb`
  `:1330`; `R1-BX-D12:756`. The census's `:95` rev attribution for `R1-TRACKG-G0-GO` is correct.
- The autoresearch bullet's remaining facts are correct: option A authorized by `R1-TRACKG-AR-COND7`; CPU-buffer
  result path + `torch.cuda.init()`; estimated 97–161 s transfer and 2.4–3.4× the 67.901 s B1 (matches the AR
  review M1 `:268-282`); "joins only after isolated smoke + U2 review pass" matches G3-EARLY. (The 17 Nov U2
  result `TRACKG_U2_AR_RESULT_20261117.md:3,44` is PASSED `CHECKLIST_E_PASSED`, B1 67.901 s.)

---

## 2. Findings

### M1 — MAJOR (remaining): U4 row-field closure incomplete — HousePrice row still 13 cells; disk and UUID/cpuset fields not carried

`TRACKG_U4_CENSUS_20261120.md:20` has 13 cells against the 14-cell header (`:12-13`): the
`whole-smoke upper bound` column is missing, `n/a (CPU, 8 cpus)` sits in it, and the committed pin `88d359f2…`,
manifest `73ee5597…` and record path are each shifted one column left (record column empty). The 599,392 kB RAM
bound never appears in the row. Separately, the `disk before/after` column (`:26-32`) carries values only for
HousePrice and defers the other six rows to captures, and the `GPU/cpus` column carries no UUIDs and no cpusets.
Round-1 M1 (`:161-183`) / C2 (`:245-247`) and the accepted five-node review §8
(`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md:500-509`) require these row fields. **Fix before acceptance.** This is
a presentation/deliverable defect only — the underlying records are complete and correct (§1.4).

### m1 — MINOR: metric-key labelling still incomplete

`TRACKG_U4_CENSUS_20261120.md:14-18`: the B1-metric cells name `val_accuracy`, but the B2-metric cells for the
five accuracy rows are bare (`0.5152`, `0.9048`, `0.275982`, `0.491`, `0.861667`) and the five sealed-test
cells are bare (`0.5015`, `0.89924`, `0.238442`, `0.4926`, `0.8515`) without `test_accuracy`. Breakout and
HousePrice do name `(test_return)`/`(test_rmse)`. Round-1 C3 (`:248-250`) asked for B1/B2 `val_accuracy` naming
with the sealed `test_accuracy` kept separate.

### m2 — MINOR: GPU UUID and cpuset not carried

`TRACKG_U4_CENSUS_20261120.md:14-20`: `GPU/cpus` = `card 1/2/6/7/2/6` and `n/a (CPU, 8 cpus)` only. The stable
UUIDs (`GPU-aa340032-6f94-9783-8f3d-50a15da47a6f`, `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`,
`GPU-3b36edea-1a09-a37e-aa42-8277c7319e77`, `GPU-3719bd35-06de-4674-7c7a-e56136fed589`) and cpusets (`0-7`,
`8-15`, `79,78,77,76,59,42,34,28`) are in the records (`limits.gpu_uuids`/`limits.cpu_list`; each
`gpu/gpu_before.txt` index table confirms the card index) but not in the census. VRAM-vs-RAM units are now
labelled in prose (`:41-43`), which closes that half of round-1 m2.

### m3 — MINOR: autoresearch status is stale (branch is pushed) and the code-unit report is cited without sha/path

`TRACKG_U4_CENSUS_20261120.md:80-81` says "branch local-only and unpushed at the time of this census". As of
this review `origin/mac-trackg-iso-ar-cond7a-20261120` is at `7330338` (reflog: "update by push",
2026-11-20T22:28:36Z), and the cond7a smoke prep already fetched it from origin at 22:31:17Z
(`ar_cond7a_smoke_20261120T223548Z/prep/worktree.txt`); the census's last write is 22:46:10Z, so the clause is
stale/false at its own write time. Also `:81` cites `TRACKG_AR_COND7A_CODE_UNIT_20261120.md` by bare filename
with no sha — the report does not exist in this worktree (it is at
`.claude-worktrees/harness_ar_cond7_20261120/docs/r1/reports/trackg_g0_20261117/`, sha `370782ab…` at tip
`7330338`; reviewed revision `13786d1f` report sha `4f1f4fe0…`), and the cited AR review (`:78`) names the path
but omits its sha `261a03e9…`. Round-1 C4 (`:251-254`) asked for these. (Status note: an isolated cond7a smoke
launch staging dir exists — `ar_cond7a_smoke_20261120T223548Z/launch_attempt1.log` `start=2026-11-20T22:35:48Z` —
so `:82` "pending an idle GPU" is also a snapshot that should be re-stated when the smoke result lands; this is
a state-timing note, not a record defect.)

### m4 — MINOR: "U2 not run" opener remains imprecise

`TRACKG_U4_CENSUS_20261120.md:77`: "U2 not run". The accurate statement is in the same bullet at `:83-84`
("The 17 Nov un-isolated U2 passed (B1 67.901 s); the **isolated** autoresearch U2 is not run"), so the
requirement is met in substance; drop/reword the `:77` shorthand to "isolated U2 not run".

### m5 — MINOR: isolation fix review cited without sha/verdict

`TRACKG_U4_CENSUS_20261120.md:67-69` cites the fix report with sha `0ff9a7f2…` and correctly says the host-check
record is the pre-fix STOP superseded by the fix report. The fix review (`HARNESS_ISOLATION_FIX_REVIEW_20261119.md`,
sha `c8e468c7…`, ACCEPTED, condition 6 PASS / condition 7 BLOCKED at `:8-10`) is cited by filename only; add its
sha and verdict for the chain to be checkable.

### m6 — MINOR: licence/availability columns are per-suite prose only

`TRACKG_U4_CENSUS_20261120.md:43-47` compresses the licence/provenance lines per suite ("MLAgentBench
tasks/IMDb/OGB arXiv generic citation") rather than per node; there is no availability status/column, although
U1 says it supplies the U4 census's licence/availability columns (`U1_LICENCE_AVAILABILITY_20261117.md:239,
264-266`). The MLAgentBench code licence (MIT, verified) and the per-item CIFAR-10/IMDb/OGB arXiv statements are
not separately stated. Round-1 m7/C6 (`:219-222`, `:259-261`).

### m7 — MINOR: authority/acceptance citations are names-only and incomplete

`TRACKG_U4_CENSUS_20261120.md:93-101` names the plan rows, kit-update report/review, result reviews and
HousePrice unit/reviews, but cites no shas, does not cite the per-node unit reviews (e.g.
`TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha `99daf16d…`) and does not cite the U4 basis docs
(`TRACKG_G0_ADA_CENSUS_20261116.md`, `TRACKG_CENSUS_20261117.md`) or the U1 audit. Round-1 m8/C6.

### m8 — MINOR: imdb disclosure is not the mandated verbatim sentence and one clause is self-referential

`TRACKG_U4_CENSUS_20261120.md:51-54` carries the substance (written by us / DistilBERT / MLAgentBench skeleton /
frozen, reviewed, disclosed), which closes B1; but the mandated wording
(`TRACKG_PORT_ISOLATION_20261117.md:98-99`: "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us;
MLAgentBench ships only a skeleton for this task.") is not reproduced verbatim, and the trailing clause "the
census/paper appendix must carry this disclosure" is self-referential inside the census appendix (it reads as an
open obligation rather than the disclosure). Use the mandated sentence for both the census and the paper
appendix.

---

## 3. Conditions for acceptance (documentation only — no new run, no record/measurement edit)

- **C1 (closes M1).** Rebuild the `mlgym_houseprice` row to exactly 14 cells with the header order: put the RAM
  bound **599,392 kB** in `whole-smoke upper bound` (labelled RAM; there is no VRAM bound for this CPU node), put
  the CPU cpuset (`79,78,77,76,59,42,34,28`) in `GPU/cpus`, then committed pin `88d359f2…`, manifest `73ee5597…`
  and record path in the remaining columns; verify no column shift with a mechanical cell count of all seven rows
  (14 cells each).
  Also add the six missing disk before/after values (`disk_before.txt`/`disk_after.txt`, `/dev/md0p3` free B) to
  the second table, and the per-node GPU UUID + cpuset to the `GPU/cpus` column (or a per-node identity column).
- **C2 (closes m1/m2).** Name `val_accuracy` in the B2-metric cells of the five accuracy rows and `test_accuracy`
  in the sealed column (as Breakout/HousePrice do with `test_return`/`test_rmse`), and state units/IDs
  (UUID, cpuset, VRAM vs RAM) in the table header/cells.
- **C3 (closes m3/m4).** Correct the autoresearch status: the branch is **pushed** at `7330338` on
  `origin/mac-trackg-iso-ar-cond7a-20261120` (2026-11-20T22:28:36Z) at the time of this writing; say so or date
  the snapshot. Cite the AR review with sha `261a03e9…`, the code-unit report with sha `370782ab…` (tip) /
  `4f1f4fe0…` (reviewed `13786d1f`) and its worktree path, and reword `:77` to "isolated U2 not run".
- **C4 (closes m5).** Cite `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` (ACCEPTED; condition 6
  PASS / condition 7 BLOCKED) alongside the already-cited fix report `0ff9a7f2…`, keeping the pre-fix host-check
  note.
- **C5 (closes m6/m7/m8).** Add the per-node licence/availability columns (including the MLAgentBench MIT code
  licence and the CIFAR-10/IMDb/OGB arXiv per-item statements and availability status), the acceptance/authority
  citations with shas and the U4 basis docs, and use the mandated verbatim imdb sentence in both the census
  appendix and the paper appendix.

After C1–C5 the census should be re-reviewed (fresh reviewer; this review is not a re-review and authorises no
run, no record edit, no commit/push, no census launch, no T1/G.1b/G.4 action). Nothing in this review changes a
measured number, pin, manifest, gate capture or isolation record; the seven rows remain supported by the
accepted records.

---

## 4. Attestation

Read-only review. The only file written is this review (uncommitted/untracked); no smoke/U2/GPU/Ada/SSH/
HTCondor/deepthought action; no unit, result, capture, record, pin, manifest, census or review was edited; no
commit/push/delete. Commands used (all read-only, 20 November 2026, Europe/Berlin): `sha256sum`/`shasum` of the
census, result mds, `SHA256SUMS`, reviews and reports named above; `wc`, `ls`, `sed`, `grep`, `awk`, `stat`,
`git show/rev-parse/log/branch/status/merge-base --is-ancestor/for-each-ref/show -s` in this worktree and the
sibling `harness_ar_cond7_20261120` worktree; Python `json` reads of all 63 `run_record.json` files (56 executed
+ 7 refused `s001`) and of each gate JSON; Python comparison of every census row value against the run records,
`time_v.txt`, result mds, pins and manifests; a mechanical markdown cell-count of both census tables
(HousePrice row 15 `|`-fields vs 16 for the header, i.e. 13 vs 14 cells); verification that each result-md entry
in `SHA256SUMS` matches the actual file and that HousePrice's corrected result md is `0b1212e3…` with
`SHA256SUMS` `7607fc5c…`. No live-host state is claimed beyond what the preserved records and local git state
contain.
