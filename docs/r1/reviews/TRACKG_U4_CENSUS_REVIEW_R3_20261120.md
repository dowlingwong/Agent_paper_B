# Independent review (round 3) — Track G U4 census (`TRACKG_U4_CENSUS_20261120.md`) — 20 November 2026

**Reviewer role.** Fresh, independent, read-only third-round reviewer (`u4-census-reviewer-r3`), delegated after
the round-2 review returned NOT ACCEPTED. No involvement in the seven U2 units/results, the isolated-kit update,
the isolation fix/code unit, the autoresearch option-A code unit/smoke, the census, or the round-1/round-2
reviews. Read-only: the only file written is this review (uncommitted/untracked). No smoke/U2/GPU/Ada/SSH run,
no unit/result/record/census edit, no commit/push/delete, no HTCondor/deepthought/TASL. The paper records,
captures, review chain, local git state and the sibling autoresearch worktree were read only.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`39c0932a4168a5a05b57567a0fa6a88a465188564cd6e2ea3158b18593ecdd27`**, **99 lines / 9,527 bytes**, mtime
**2026-11-20T22:54:58Z** (23:54:58 local), uncommitted/untracked at worktree HEAD **`30cadb81`** (branch
`ops-tasl-20261116`). Round-1 object was sha `7774a465…` (56 lines; review
`TRACKG_U4_CENSUS_REVIEW_20261120.md`, sha `f8ffe193…`, 282 lines). The round-2 review
(`docs/r1/reviews/TRACKG_U4_CENSUS_REVIEW_R2_20261120.md`, sha **`04b5893c…`**, 324 lines) reviewed the revision
its header records as sha **`f6c226b7…`, 101 lines**. That revised-in-place revision is **not preserved** anywhere
in the workspace (the census is untracked and was rewritten at 22:54:58Z), so the R2→R3 delta cannot be audited
byte-for-byte; this review checks the final object and the claims it makes (finding m9).

**Authority / inputs read.**
- PLAN rows at the cited revisions: `R1-TRACKG-G0-GO` (`de3de54f` `:1258`; worktree `:1258`), `R1-TRACKG-LICENCES`
  (`:1269`), `R1-TRACKG-PORT-DECISIONS` (`:1289`), `R1-HARNESS-ISOLATION` (`:1290`), `R1-TRACKG-AR-COND7`
  (`:1317`), `R1-TRACKG-G3-EARLY` (`:1330`, added at `94db94bb`; the PLAN at `de3de54f` has only 1317 lines).
- G.0/U4 basis: `TRACKG_G0_ADA_CENSUS_20261116.md`, `TRACKG_CENSUS_20261117.md`,
  `U1_LICENCE_AVAILABILITY_20261117.md` (§7 per-node licence/availability table, §8).
- The seven result directories `u2_iso_*_2026111*Z` / `u2_iso_mlgym_houseprice_20261120T215244Z/`: result mds,
  `SHA256SUMS` (verified with `shasum -a 256 -c`), all 63 `run_record.json` (7×9 = 56 executed + 7 refused `s001`),
  `pins.txt`, `verify_full.json`, `summary.json`, `time_v.txt`, `cgroup_probe.txt`, `gate/*.json`,
  `data_manifest.txt`, `disk_before.txt`/`disk_after.txt`, `gpu/*`, `cpu/*`, `attempt1_prelaunch_*/`,
  `DONE`/`RESULT_STATUS.txt`, `prep/`.
- The autoresearch option-A smoke directory `ar_cond7a_smoke_20261120T223548Z/` (untracked; `DONE`,
  `RESULT_STATUS.txt`, `U2_ISO_AR_COND7A_RESULT_20261120.md` sha `bcb74efc…`, `slowdown.json`,
  `failure_time_census.txt`, `gate/`, `gpu/`, `cgroup_probe.txt`) and the sibling harness worktree
  `.claude-worktrees/harness_ar_cond7_20261120` (branch `mac-trackg-iso-ar-cond7a-20261120`: local HEAD
  `7330338`, `origin/…` = `7330338` "update by push"; report sha `370782ab…` at `7330338`, `4f1f4fe0…` at
  `13786d1f`).
- Accepted reviews: `TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (`965dc993…`, §8 census-row support),
  `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` (`d4cdd9bb…`),
  `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` (`b2c463a7…`), `TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`
  (`d8c68f9f…`), `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (`c8e468c7…`, ACCEPTED; condition 6 PASS /
  condition 7 BLOCKED), `HARNESS_ISOLATION_FIX_20261119.md` (`0ff9a7f2…`),
  `HARNESS_ISOLATION_HOST_CHECK_20261119.md` (`6a700509…`, pre-fix STOP),
  `TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` (`261a03e9…`, 403 lines), the unit reviews
  (`TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha `99daf16d…`, etc.), and the three accepted correction notes
  (`U2_ISO_RECORD_CORRECTIONS_20261119.md`, `U2_ISO_BREAKOUT_RECORD_CORRECTIONS_20261119.md`,
  `U2_ISO_HOUSEPRICE_RECORD_CORRECTIONS_20261120.md` — all "corrections APPLIED").

---

## Verdict: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 9 MINOR

The round-2 **MAJOR is closed**: the `mlgym_houseprice` row now has **14 cells matching the 14-cell header**
(`:20` vs `:12-13`, mechanical `awk -F'|'` = 16 fields for all seven rows), the six missing disk before/after
values and the per-node GPU UUIDs + cpusets are carried (§1.1), and all seven rows' measured values (B1/B2,
sealed metric, 3×B1 timeout, max RSS, VRAM bound, committed/deployed pins, manifest, gate capture, UUID/cpuset,
disk) recompute **exactly** from the preserved records and captures (§1.4). **No fabricated row, no overclaimed
number, no measurement defect remains.**

However, the census's autoresearch status is now **materially false**: it says the isolated Ada GPU smoke is
"pending an idle GPU; it will measure the slowdown" (`:58-59`, `:79-81`), while the one authorized isolated smoke
was in fact **attempted, consumed and STOPPED at 2026-11-20T22:54:22Z** (baseline CUDA OOM caused by a co-tenant
that started on the launch card ~3 min after launch), with **no retry**, **no transfer measurement**, and any new
smoke requiring fresh coordinator authorization. The census's final write (22:54:58Z) is 36 s after that STOP
record landed; the full result record is now in the tree. This misstates a T1/G.1b/G.4 candidate's status in the
"Blocked / not passed" section and must be corrected before acceptance (**M1**). The remaining nine items are
MINOR documentation/citation/labelling residuals (m1–m9); they do not touch a measured number.

---

## 1. Closure verification

### 1.1 R2 M1 (HousePrice row cells/fields) — **CLOSED**

Mechanical check (`awk -F'|'` on `:12-20`): header and **all seven data rows have 16 `|`-fields = 14 cells**;
the second table (`:24-32`) has 5 cells per row. The previous column shift is gone.

- **`mlgym_houseprice` row (`:20`)**: `n/a (CPU)` in *whole-smoke upper bound*, `cpus 79,78,77,76,59,42,34,28`
  in *GPU/cpus*, committed pin `88d359f2…`, manifest `73ee5597…`, record
  `u2_iso_mlgym_houseprice_20261120T215244Z/` — each in the correct column; **no shift, record column filled**.
- **Whole-smoke max RSS for all seven** (`:24-32`, header `:24` "whole-smoke max RSS (kB)"): 1,402,612 /
  1,659,008 / 1,256,776 / 1,493,864 / 1,213,024 / 1,262,488 / **599,392** — each equals the corresponding
  `time_v.txt` "Maximum resident set size (kbytes)" and the result md (§1.4).
- **Disk before/after actual values for all seven** (`:26-32`): recomputed from each `disk_before.txt`/
  `disk_after.txt` `/dev/md0p3` Available bytes — mlab_cifar10 `74,632,835,072 -> 74,630,283,264`; mlab_imdb
  `74,629,115,904 -> 74,609,201,152`; mlab_ogbn_arxiv `74,610,388,992 -> 74,605,633,536`; mlgym_cifar10
  `74,604,687,360 -> 74,597,408,768`; mlgym_fmnist `74,596,868,096 -> 74,548,490,240`; breakout
  `75,439,427,584 -> 75,401,625,600`; houseprice `70,644,187,136 -> 70,795,374,592` — **all match**.
- **GPU UUID + cpuset for all seven** (`:14-20`): UUIDs match `limits.gpu_uuids` and the `gpu/gpu_before.txt`
  index tables (card 1 = `GPU-aa340032…`, 2 = `GPU-f439cca8…`, 6 = `GPU-3b36edea…`, 7 = `GPU-3719bd35…`);
  cpusets match `limits.cpu_list` (`0-7` ×3 mlab, `8-15` ×3 mlgym, HousePrice `79,78,77,76,59,42,34,28`).
- **Deployed run-record pins** (`:26-32`) match `pins.txt` / `verify_full.json` / the records
  (`a459b3d8…`, `c169a6b8…`, `5ff5824a…`, `817c9034…`, `ef804338…`, `cec562e6…` = committed for Breakout,
  `4cbbc5d6…`); **committed-file pins** (`:14-20`) match `pins.txt` (`1f047ad7…`, `4b1019a6…`, `bd71fdf4…`,
  `2d7e533b…`, `eb60107e…`, `cec562e6…`, `88d359f2…`).
- **Gate captures** (`:26-32`): all seven paths resolve; every gate JSON is `verdict: clear_finished`,
  `paper_a_live_waiting_for_card: false`, `evidence.gpu.paper_a_processes: []`, UTC stamp.

R2 condition C1's literal instruction for the bound cell ("put the RAM bound 599,392 kB in `whole-smoke upper
bound`, labelled RAM") is met only **indirectly**: the cell reads `n/a (CPU)` and 599,392 kB is in the run-level
table. That is a labelling/compliance residual (m2), not the M1 defect (the value is in the census and the row
no longer shifts).

### 1.2 Minor closures from round 2

| round-2 item | status | note |
|---|---|---|
| m1 metric-key labelling | **partial** | `val_accuracy` now named in B1 **and B2** cells of the five accuracy rows (`:14-18`); sealed cells still bare; B2 cells bare for Breakout/HousePrice (`:19-20`) — see m1 |
| m2 GPU/cpuset not carried | **closed** | UUIDs + cpusets now in `GPU/cpus` (`:14-20`) |
| m3 AR pushed/sha/path | **closed on those facts** | "branch pushed to origin", reviewed `13786d1f`, review sha `261a03e9…`, report sha `370782ab…` (`:78-79`) all verified; but the status clause is now false — see **M1** |
| m4 "U2 not run" opener | **open** | `:76-77` — see m3 |
| m5 fix-review sha/verdict | **partial** | sha `c8e468c7…` added, ACCEPTED verdict missing, filename duplicated (`:67-68`) — see m4 |
| m6 per-node licence/availability | **open** | still per-suite prose (`:44-47`, `:55-57`) — see m5 |
| m7 authority/acceptance citations | **open** | names only, no shas, per-node unit reviews/basis docs missing; "six … reviews" mismatch (`:93-99`) — see m6 |
| m8 imdb verbatim wording | **open** | `:51-54` — see m7 |
| (round-1 m9 relative paths) | **closed** | base path `docs/r1/reports/trackg_g0_20261117/` at `:22`, `:99`; all seven record dirs resolve |

### 1.3 Artifact integrity (read-only re-verification)

- **Result dirs**: `shasum -a 256 -c SHA256SUMS` rc 0 in all seven (428 / 427 / 426 / 426 / 426 / 1117 / 447
  entries OK, 0 failures); HousePrice result md sha `0b1212e3…` and `SHA256SUMS` sha `7607fc5c…` match the
  accepted-correction note.
- **Records**: every dir has exactly 9 `run_record.json` = **8 executed + 1 refused `s001`** (`executed:false`,
  `scope_violation` on the frozen `run_fixed_budget.py` diff); every executed record has
  `isolation.effective:true`, `isolation.waivers {}`, `isolation.exceptions []`, `isolation.log_intact:true`,
  a result-channel sha, `cgroup.kill.empty_after:true`/`removed:true`, `process.timed_out:false`; every
  `cgroup_probe.txt` shows inside-scope `memory.max=8589934592`, `memory.swap.max=0`; `CHECKLIST_E_PASSED`
  present in each `smoke_stdout_extract.txt`.
- **Data manifests**: `43fdf860…`, `a87254e1…`, `91312162…`, `c0ef1168…`, `8d28287b…`, Breakout `none
  (simulated)`, HousePrice `73ee5597…` — all match the census; `synthetic` marker absent/n-a; data paths outside
  the repo.
- **Attempt-1 refusals**: `attempt1_prelaunch_cpu_idle_stop/` ("mean idle 70.6 % < 80 %; no smoke launched") and
  `attempt1_prelaunch_gate_stop/` ("gate three-check not clear … no smoke launched") preserved; disclosed at
  `:60-61`.
- **No fabricated/extra row**: exactly the seven `u2_iso_*` directories referenced by the census exist, and the
  census references exactly those seven.
- **Kit tips**: `kit.txt` in the three mlab dirs = `fb6e7d73…`; the three mlgym dirs + HousePrice =
  `f07875de…`; the accepted kit-update report (current sha `fe232e2b…`; reviewed as `3c3ae74a…` plus
  C-K1–C-K4) records both branches carry the accepted isolation core fix `5403392e` merge + node copies/pins;
  envs = `torch312` (five torch nodes + HousePrice) and `jax312`
  (jax 0.4.35, `nvidia-cuda-nvcc-cu12` absent; Breakout).

### 1.4 Independent recomputation of the seven rows (all values verified)

| node | B1 s / value | B2 s / value | sealed | 3×B1 | max RSS kB | VRAM bound MiB | committed / deployed | GPU / cpus | manifest |
|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 / 0.5152 | 11.846 / 0.5152 | 0.5015 test_accuracy | 36.891 | 1,402,612 | 836 | `1f047ad7` / `a459b3d8` | aa340032 (1) / 0-7 | `43fdf860` |
| mlab_imdb | 64.142 / 0.9048 | 64.133 / 0.9048 | 0.89924 test_accuracy | 192.426 | 1,659,008 | 11,292 | `4b1019a6` / `c169a6b8` | f439cca8 (2) / 0-7 | `a87254e1` |
| mlab_ogbn_arxiv | 5.651 / 0.275982 | 5.665 / 0.275982 | 0.238442 test_accuracy | 16.953 | 1,256,776 | 4,544 | `bd71fdf4` / `5ff5824a` | 3b36edea (6) / 0-7 | `91312162` |
| mlgym_cifar10 | 31.731 / 0.491 | 31.244 / 0.491 | 0.4926 test_accuracy | 95.193 | 1,493,864 | 982 | `2d7e533b` / `817c9034` | 3719bd35 (7) / 8-15 | `c0ef1168` |
| mlgym_fmnist | 34.376 / 0.861667 | 28.868 / 0.861667 | 0.8515 test_accuracy | 103.128 | 1,213,024 | 912 | `eb60107e` / `ef804338` | f439cca8 (2) / 8-15 | `8d28287b` |
| mlgym_breakout_minatar | 61.248 / 22.486719 | 61.781 / 22.486719 | 22.885938 test_return | 183.744 | 1,262,488 | 634 | `cec562e6` / `cec562e6` | 3b36edea (6) / 8-15 | none (simulated) |
| mlgym_houseprice | 5.059 / 23344.767385 | 4.876 / 23344.767385 | 30295.671017 test_rmse | 15.177 | 599,392 | n/a (CPU) | `88d359f2` / `4cbbc5d6` | CPU cpuset 79,78,77,76,59,42,34,28 | `73ee5597` |

- All B1/B2 elapsed and values, and all sealed values, equal `run_record.json`
  (`elapsed_seconds_info_only`, `outcome.value`, `sealed`); the census's `3×B1` equals 3 × B1 exactly for all
  seven; max RSS equals `time_v.txt`; VRAM bounds equal the result mds' labelled whole-smoke sampler upper bounds
  (836 / 11292 / 4544 / 982 / 912 / 634 MiB); the deployed pin is constant across all executed records per node
  and matches `verify_full.json`; HousePrice `gpu_uuids: []` (CPU), cpuset matches `limits.cpu_list`.
- The three accepted record-correction notes are marked APPLIED before the census-row write; the accepted
  five-node review §8 (which requires the U4 row to carry the committed-file pin as the census value and the
  deployed pin separately, B1/B2, 3×B1, the whole-smoke CPU/RAM aggregate, the labelled sampler upper bound, disk
  before/after, the gate capture and the isolation fields) and the Breakout/HousePrice review conditions are
  satisfied by the rows as corrected.

### 1.5 Autoresearch bullet — facts that are correct, and the one that is not

The R2 m3 facts are now accurate and verified: `origin/mac-trackg-iso-ar-cond7a-20261120` is at **`7330338`**
(reflog "update by push"); the code was reviewed at **`13786d1f`**; the code review
`docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha **`261a03e9…`** is **ACCEPTED for the code change
— 0 BLOCKING, 1 report-only MAJOR, 6 MINOR, conditions C1–C6**; the report at the fix tip is
**`370782ab…`** (`7330338` changes docs/captures only; `13786d1f` report sha `4f1f4fe0…`); the 17 Nov
un-isolated U2 passed with B1 67.901 s; the **isolated** autoresearch U2 is not run. The corrected §8 estimate
(644 requests, ≈97–161 s/run, ≈2.4–3.4× B1) is the right estimate to quote.

**What the census gets wrong** is the smoke status (see M1): the one isolated smoke required by C2 was run and
STOPPED; the census says it is still "pending an idle GPU" and "will measure the slowdown".

### 1.6 Readiness / labels / authority

- **G3-EARLY** (`94db94bb`/worktree `:1330`): six nodes set now for G.1b/G.4 (`mlab_cifar10, mlab_imdb,
  mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist, mlgym_breakout_minatar`); `mlgym_houseprice` joins as its U2
  passes (result review ACCEPTED `b2c463a7…`, corrections applied — so "HousePrice joins now" `:87` is correct);
  autoresearch joins after its U2 passes. The census's readiness sentence (`:87-88`) is correct; the G.4 pilot
  in that row designates `autoresearch_fixedtokens` as the third pilot node with `mlgym_breakout_minatar` as the
  fallback "if autoresearch is not ready" — which is exactly why the stale AR status matters (M1).
- **ENGINEERING_ONLY / no evidence / no noise floor / no D21 / no D28 / no T1 label / no HTCondor/deepthought**
  (`:3-8`, `:43-44`, `:89`) — correct; every result/unit carries the same labels; no claim to the contrary.
- **Kit tips/fix**: `fb6e7d73…` / `f07875de…` verified from `kit.txt`; the kit-update report records the
  `5403392e` merge; env statements (`torch312`, `jax312`/jax 0.4.35) match the records.
- **Authority lines**: `de3de54f` `:1258/:1269/:1289/:1290` and `94db94bb`/worktree `:1330` verified; condition 6
  PASS / condition 7 BLOCKED claims match the accepted fix report/review.

---

## 2. Findings

### M1 — MAJOR: the autoresearch status is materially false (smoke consumed and STOPPED, census says "pending an idle GPU")

The census says:

- `:58-59` — "**autoresearch (1 node):** not in this census; condition-7 option-A code unit accepted, isolated
  smoke pending an idle GPU; joins after smoke+U2."
- `:79-81` — "An isolated Ada GPU smoke is **pending an idle GPU; it will measure the slowdown** (estimated
  97–161 s transfer per run, 2.4–3.4× the 17 Nov B1 67.901 s)."

The preserved record says the opposite: the one authorized isolated Ada smoke was **launched 2026-11-20T22:35:48Z**
(card 5, `GPU-5357dc5f…`, verified idle), the baseline then died with **`torch.OutOfMemoryError` during
evaluation** because another user's job (9 GPU processes, ≈42.6 GiB) started on the same card ≈3 min after launch,
and the smoke was **deliberately STOPPED at 22:54:22Z** (`DONE` = `DONE_STOP 2026-11-20T22:54:22Z`;
`RESULT_STATUS.txt` = `status=STOP`, `systemd_run_rc=137`, `checklist_e_passed=0`;
`U2_ISO_AR_COND7A_RESULT_20261120.md` sha `bcb74efc…` status **STOP**; `slowdown.json` failed-run numbers,
explicitly not a transfer measurement). `CHECKLIST_E_PASSED` was not reached, the expected 8 executed records/B2
were not reached, the **logits-transfer slowdown was NOT obtained** (748.79 s failed-run wall and the 1.057 s
surrogate are invalid as measurements), and **no retry was performed** (one smoke only); the result record states
a new isolated smoke **"would need fresh coordinator authorization and a card guaranteed idle for the whole
run"** (§6.5). The census's final write is **36 s after** the STOP record landed (`DONE`/`RESULT_STATUS` mtime
22:54:22Z; census mtime 22:54:58Z), and the full result record is now present.

This is not the R2 "state-timing note" any more: it is an affirmative claim that the smoke is still to run and
will produce the measurement, in the very section that must carry blocked/not-passed status, for the node
G3-EARLY designates as the third G.4 pilot (breakout fallback "if autoresearch is not ready"). **Fix before
acceptance** (docs-only; no new run is required for the census). Everything else in the AR bullet (pushed at
`7330338`, reviewed `13786d1f`, code-review sha/ACCEPTED/1 report-only MAJOR + 6 MINOR/C1–C6, report `370782ab…`,
17 Nov un-isolated U2 passed, isolated U2 not run, join condition) is accurate and should be kept.

### m1 — MINOR: metric-key labelling is still incomplete

`:14-18`: the B1 **and** B2 cells now name `val_accuracy` (R2 m1's B2 half closed), but the **sealed-test cells
of the five accuracy rows are still bare** (`0.5015`, `0.89924`, `0.238442`, `0.4926`, `0.8515`) without
`test_accuracy`, and the B2 cells for Breakout (`:19`) and HousePrice (`:20`) are bare (`22.486719`,
`23344.767385`). Breakout/HousePrice do name `test_return`/`test_rmse`. R2 C2 asked to name `test_accuracy` in the
sealed column and to state the metric keys; finish it (the values are correct).

### m2 — MINOR: the HousePrice "whole-smoke upper bound" cell and the disk/units labelling

`:20` puts `n/a (CPU)` in *whole-smoke upper bound*, while the **599,392 kB RAM bound is only in the run-level
table** (`:32`); the column header (`:12`) does not say VRAM. R2 condition C1 asked for the RAM bound in the
bound column, labelled RAM. Either put `599,392 kB (RAM)` / `n/a VRAM (CPU node); RAM 599,392 kB below` in the
cell, or rename the column to "whole-smoke VRAM upper bound". Also: the disk before/after cells (`:26-32`) carry
actual byte values but no unit (`B`), and `:34-36` still says "disk before/after … are in the record captures"
although the table now carries them (stale wording).

### m3 — MINOR: "U2 not run" shorthand remains

`:76-77` still opens "isolation condition 7 … fails on Ada; U2 not run". The precise sentence ("The 17 Nov
un-isolated U2 passed (B1 67.901 s); the **isolated** autoresearch U2 is not run") is `:81-82`; drop/reword the
opener to "isolated U2 not run" (R2 m4).

### m4 — MINOR: isolation-fix review cited with sha but without its ACCEPTED verdict, and the filename is duplicated

`:67-68`: the fix review is cited with sha `c8e468c7…` (R2 m5's sha half closed) but no verdict, and
`HARNESS_ISOLATION_FIX_REVIEW_20261119.md` is listed twice (the second occurrence without sha). The substantive
claims — condition 6 PASS, condition 7 GPU CUDA-IPC BLOCKED/disclosed, fix report supersedes the pre-fix host
check — match `HARNESS_ISOLATION_FIX_20261119.md` (`0ff9a7f2…`) and `HARNESS_ISOLATION_FIX_REVIEW_20261119.md`
(`c8e468c7…`, ACCEPTED, condition 6 PASS / condition 7 BLOCKED). Add "ACCEPTED" and remove the duplicate.

### m5 — MINOR: licence/availability remains per-suite prose, not the per-node columns

`:44-47` and `:55-57` compress the licence/provenance lines per suite ("MLAgentBench tasks/IMDb/OGB arXiv generic
citation; MLGym CC BY-NC 4.0 with notice and gymnax-blines Apache-2.0 parts used only by Breakout; HousePrice …
`--from-file`, no MLGym copy"). `U1_LICENCE_AVAILABILITY_20261117.md` §7 supplies a **per-node** code licence +
asset licence + availability table (MLAgentBench code **MIT**; MLGym CC-BY-NC-4.0; CIFAR-10 unknown; IMDb
`license: other`; ogbn-arxiv ODC-BY; Fashion-MNIST MIT; gymnax Apache-2.0; Kaggle terms), and §8 says it
"supplies the U4 census's licence/availability columns". Add the per-node licence/availability columns (or a
per-node licence line) as R2 m6/C6 required; the per-node `work/LICENCES.md` files are in the records.

### m6 — MINOR: authority/acceptance citations are names-only and incomplete

`:93-99`: plan rows are cited with `de3de54f`/line numbers (G0-GO `:1258`, LICENCES `:1269`, PORT-DECISIONS
`:1289`, HARNESS-ISOLATION `:1290`, G3-EARLY `:1330`); acceptances are names only — **no shas**, no per-node unit
reviews (e.g. `TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha `99daf16d…`), no U4 basis docs
(`TRACKG_G0_ADA_CENSUS_20261116.md`, `TRACKG_CENSUS_20261117.md`) and no U1 audit citation. The phrase "six
isolated U2 result reviews" names only two files (the actual result reviews are the five-node review + Breakout
result review + HousePrice result review), and `R1-TRACKG-G3-EARLY (:1330)` is cited by line without its revision
(added at `94db94bb`; the PLAN at `de3de54f` has 1317 lines). The cited kit-update report is now
`fe232e2b…` while the accepted kit review (`d8c68f9f…`) records that it reviewed `3c3ae74a…`; the units carry
the convention "current sha `fe232e2b…`; reviewed `3c3ae74a…` plus C-K1–C-K4", which the census should also
state. R2 m7/C6 remains open.

### m7 — MINOR: the imdb disclosure is not the mandated verbatim sentence and its last clause is self-referential

`:51-54` carries the substance (written by us / DistilBERT-base-uncased / MLAgentBench skeleton / frozen,
reviewed, disclosed as ours) and closes the round-1 BLOCKING; but the mandated wording
(`TRACKG_PORT_ISOLATION_20261117.md:98-99`: "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us;
MLAgentBench ships only a skeleton for this task.") is not reproduced verbatim, and the trailing clause "the
census/paper appendix must carry this disclosure" reads as an open obligation inside the appendix. Use the
mandated sentence in both the census and the paper appendix (R2 m8).

### m8 — MINOR: "whole-smoke CPU/RAM aggregates labelled" overstates what the census carries

`:41` says "whole-smoke CPU/RAM aggregates labelled". The run-level table carries the **whole-smoke max RSS**
(`:24-32`), but no whole-smoke **CPU** aggregate (the `time -v` user/system/wall numbers are in the result mds,
not the census); the accepted five-node review §8 asks the U4 row for the "whole-smoke CPU/RAM aggregate". Either
carry the CPU-time aggregate or reword to "whole-smoke RAM (max RSS) labelled; whole-smoke VRAM bound labelled".

### m9 — MINOR (traceability): the R2-reviewed revision is not preserved

The R2 review's object (per its header: sha `f6c226b7…`, 101 lines) is not present in the workspace: the census is
untracked and was revised in place at 22:54:58Z, so the R2→R3 delta cannot be verified byte-for-byte (this review
recomputes every value from the records instead, which is how the R2 MAJOR closure above is established).
Acceptance should bind to the exact reviewed sha (`39c0932a…`) and commit/preserve it; if the file changes again,
that revision needs a fresh review (or a preserved copy + delta) rather than an in-place rewrite.

---

## 3. Conditions for acceptance (documentation only — no new run, no record/measurement edit)

- **C1 (closes M1).** Rewrite the autoresearch status at `:58-59` and `:76-84`: the one authorized isolated Ada
  smoke was launched 22:35:48Z and **STOPPED at 22:54:22Z** (baseline CUDA OOM; a co-tenant started on the launch
  card ≈3 min after the idle verification; no CUDA-IPC error; isolation `effective:true`, `waivers {}`,
  `exceptions []`, private `/dev/shm`; `CHECKLIST_E_PASSED` not reached; 1 executed record + refused `s001`; no
  B2), **no retry**, **slowdown not measured** (748.79 s failed-run wall and the `slowdown.json` surrogate are
  not measurements), and a **new isolated smoke needs fresh coordinator authorization + a card guaranteed idle
  for the whole run**; keep the 17 Nov un-isolated U2 pass (B1 67.901 s), "isolated U2 not run", the pushed
  branch `@7330338`, reviewed `13786d1f`, code review `261a03e9…` ACCEPTED (0 BLOCKING, 1 report-only MAJOR,
  6 MINOR, C1–C6), report `370782ab…`, and the join condition; point to the smoke result dir
  `ar_cond7a_smoke_20261120T223548Z/`.
- **C2 (closes m1).** Name `test_accuracy` in the sealed cells of the five accuracy rows and `val_return` /
  `val_rmse` in the B2 cells of Breakout/HousePrice.
- **C3 (closes m2).** Put the 599,392 kB RAM bound in (or cross-reference it from) the `mlgym_houseprice`
  `whole-smoke upper bound` cell with an explicit RAM/VRAM label; add `B` to the disk values; fix the `:34-36`
  "in the record captures" wording.
- **C4 (closes m3).** Reword `:76-77` to "isolated U2 not run".
- **C5 (closes m4).** Cite `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` with **ACCEPTED**
  (condition 6 PASS / condition 7 BLOCKED) and remove the duplicate filename.
- **C6 (closes m5).** Add the per-node licence/availability columns (U1 §7: MLAgentBench MIT code licence;
  CIFAR-10/IMDb/OGB arXiv per-item statements; MLGym CC-BY-NC-4.0 + notice; gymnax-blines Apache-2.0 for
  Breakout only; Kaggle terms for HousePrice) with the availability status.
- **C7 (closes m6).** Give shas and complete the citations: kit-update report+review, the per-node unit reviews
  (incl. `99daf16d…`), the result reviews, the U4 basis docs, the U1 audit; correct "six isolated U2 result
  reviews"; attribute G3-EARLY to `94db94bb` (or the worktree).
- **C8 (closes m7).** Use the mandated verbatim imdb sentence in the census appendix (and paper appendix) and drop
  the self-referential clause.
- **C9 (closes m8/m9).** Reconcile the "whole-smoke CPU/RAM aggregates" wording with what is carried; bind
  acceptance to the reviewed sha `39c0932a…` and preserve/commit that revision (do not revise in place after
  acceptance without a fresh review).

After C1–C9 a fresh reviewer should re-check. This review authorises no run, no record edit, no commit/push, no
census launch, no T1/G.1b/G.4 action. Nothing in this review changes a measured number, pin, manifest, gate
capture or isolation record; the seven rows remain fully supported by the accepted records.

---

## 4. Attestation

Read-only review. The only file written is this review (uncommitted/untracked); no smoke/U2/GPU/Ada/SSH/
HTCondor/deepthought action; no unit, result, capture, record, pin, manifest, census or review was edited; no
commit/push/delete. Commands used (all read-only, 20 November 2026, Europe/Berlin): `shasum -a 256` of the census,
result mds, `SHA256SUMS`, reviews, reports and the AR smoke record; `wc`, `ls`, `stat`, `sed`, `grep`, `awk`;
`git show/rev-parse/branch/status/log/for-each-ref/reflog` in this worktree and the sibling
`harness_ar_cond7_20261120` worktree; Python `json` reads of all 63 `run_record.json` (56 executed + 7 refused
`s001`), all seven gate JSONs, the seven `verify_full.json`/`summary.json`, the seven `time_v.txt`,
`disk_before/after.txt`, `pins.txt` and manifests; a mechanical markdown cell count of both census tables (all
seven rows 14 cells vs the 14-cell header; the run-level table 5 cells); and `shasum -a 256 -c SHA256SUMS` in all
seven result dirs (rc 0, 0 failures). No live-host state is claimed beyond what the preserved records and
captures and local git state contain.
