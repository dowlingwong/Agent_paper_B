# Independent review (round 5) — Track G U4 census (`TRACKG_U4_CENSUS_20261120.md`) — 20/21 November 2026

**Reviewer role.** Fresh, independent, read-only fifth-round reviewer (`u4-census-reviewer-r5`), delegated
after the round-4 review returned NOT ACCEPTED (0 BLOCKING, 1 MAJOR, 13 MINOR). No involvement in the seven U2
units/results, the isolated-kit update, the isolation fix/code unit, the autoresearch option-A code unit/smoke,
the census, or the round-1/2/3/4 reviews. Read-only: the only file written is this review (uncommitted/untracked).
No smoke/U2/GPU/Ada/SSH run, no unit/result/record/census edit, no commit/push/delete, no HTCondor/deepthought/
TASL. The paper records, captures, review chain, local git state and the sibling harness worktrees were read only.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`4e050ad22c63dde41af191a3adac678252f789da2dd56f2871755895716fa285`**, **109 lines / 11,207 bytes**, mtime
**2026-11-20T23:13:32Z** (21 Nov 00:13:32 local), **untracked** at worktree HEAD **`92ed9bb9`** (branch
`ops-tasl-20261116`; `origin/main` is `df58bcd5`, not this worktree's HEAD). This matches the sha the
coordinator named for this round. The round-4 object (`35d2c3e3…`, 109 lines / 10,263 bytes per the R4 review)
is **not preserved** — the only census copy in the workspace is the current file and the R4 object is not a git
object — so the R4→R5 delta cannot be audited byte-for-byte; it was audited against the R4 review's verbatim
quotes plus a full independent recomputation from the preserved records. The revision was written in place at
23:13:32Z, **52 s after the R4 review file's mtime** (23:12:40Z) and 4 s before this reviewer session started
— i.e. the in-place-rewrite traceability problem (R4 m9) recurred.

**Authority / inputs read.**
- The R4 review `docs/r1/reviews/TRACKG_U4_CENSUS_REVIEW_R4_20261120.md` (sha **`acb80d68…`**, 337 lines),
  R3 review (`a18c02cb…`, 356 lines), R2 review (`04b5893c…`, 324 lines) and R1 review (`f8ffe193…`, 282 lines).
- The committed autoresearch result directory at HEAD `92ed9bb9`
  `docs/r1/reports/trackg_g0_20261117/ar_cond7a_smoke_20261120T223548Z/` (committed tree: 1,789 files):
  `DONE`, `RESULT_STATUS.txt`, `U2_ISO_AR_COND7A_RESULT_20261120.md` (sha **`bcb74efc…`**), `SHA256SUMS` (sha
  **`231d388e…`**, 1,800 entries), `failure_time_census.txt`, `gate/gate_20261120T223548Z.json`,
  `gpu/{gpu_qualify,gpu_before,gpu_mid,gpu_after}.txt`, `slowdown.json`, `summary.json`, `verify_full.json`,
  `runs/runs_smoke/s000_baseline/run_record.json` and `s001/run_record.json`, `pins.txt`,
  `prep/pins_{committed,deployed}.txt`, `cgroup_probe.txt`, launch logs, and the code unit/review
  (`TRACKG_AR_COND7A_CODE_UNIT_20261120.md` sha **`370782ab…`**, `TRACKG_AR_COND7A_CODE_REVIEW_20261120.md`
  sha **`261a03e9…`**). Both are committed at HEAD; the unit's cited report tip is `7330338` and the
  `harness_ar_cond7_20261120` worktree's `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120` = `7330338`
  (supports the census's "pushed").
- The seven isolated U2 result directories `u2_iso_*_2026111*Z` / `u2_iso_mlgym_houseprice_20261120T215244Z/`:
  all `run_record.json` (7 dirs × 9 records = 63: 56 executed + 7 refused `s001`; the executed set includes
  B2/E1–E4 in `runs_edits/`), `SHA256SUMS`,
  `pins.txt`, `verify_full.json`, `summary.json`, `time_v.txt`, `disk_before.txt`/`disk_after.txt`,
  `data_manifest.txt`, `gate/*.json`, `cgroup_probe.txt`, `gpu/` or `cpu/` captures, `smoke_stdout_extract.txt`,
  attempt-1 pre-launch refusal dirs (HousePrice, Breakout).
- `docs/r1/PLAN.md` at HEAD (`R1-TRACKG-G0-GO` `:1258`, `R1-TRACKG-LICENCES` `:1269`,
  `R1-TRACKG-PORT-DECISIONS` `:1289`, `R1-HARNESS-ISOLATION` `:1290`, `R1-TRACKG-AR-COND7` `:1317`,
  `R1-TRACKG-G3-EARLY` `:1330`; 1,337 lines at HEAD/`94db94bb`/`origin/main df58bcd5`; the PLAN at
  `de3de54f` has 1,317 lines and has no `:1330` row).
- `U1_LICENCE_AVAILABILITY_20261117.md` (sha **`70d54b71…`**) §7 / §8, `TRACKG_CENSUS_20261117.md`
  (`5cd2a0cb…`), `TRACKG_G0_ADA_CENSUS_20261116.md` (`903fc8a5…`), `TRACKG_ISO_KIT_UPDATE_20261119.md`
  (`fe232e2b…`) and its review (`d8c68f9f…`, which records it reviewed `3c3ae74a…`, C-K1–C-K5),
  `HARNESS_ISOLATION_FIX_20261119.md` (`0ff9a7f2…`), `HARNESS_ISOLATION_FIX_REVIEW_20261119.md`
  (`c8e468c7…`), `TRACKG_PORT_ISOLATION_20261117.md` `:98-99` (mandated imdb sentence), the unit reviews
  (`TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` `99daf16d…`, `TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md`
  `217822fe…`, `TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md` `81580eec…`), the three result reviews
  (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` `965dc993…`, `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`
  `d4cdd9bb…`, `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` `b2c463a7…`), and the harness worktree
  `harness_ar_cond7_20261120` (read-only branch/ref checks).

---

## Verdict: ACCEPTED — 0 BLOCKING, 0 MAJOR, 10 MINOR (9 carried from R4 + 1 new)

The **R4 MAJOR (M1) is closed.** The funnel appendix no longer says the isolated smoke is "pending an idle GPU"
(`:58-60` now states it was attempted and STOPPED with an external co-tenant CUDA OOM, the slowdown was not
measured and there was no retry; the row joins after a fresh clean isolated smoke + U2 review), and no
"pending/not yet/will measure" status claim for AR remains anywhere in the census (§1). The Blocked section
(`:82-92`) matches the committed record on every material fact and adds the isolated-U2-not-run / 17 Nov
un-isolated-pass / join-condition facts. The measured seven rows are fully sound (§2): every B1/B2 elapsed and
value, sealed value, 3×B1 timeout, max RSS, VRAM upper bound, disk before/after, committed/deployed pin,
manifest, GPU UUID, cpuset, gate and record count recomputes exactly from the preserved records; all seven
`SHA256SUMS` verify rc 0; there is **no fabricated or overclaimed number, pin, manifest or record**. The census
is not yet release-clean: 9 R4 MINORs remain open or partial and the R5 edit introduced one **new formatting
regression** — the main table's delimiter row now has 14 cells under a 15-cell header, so the census's primary
table no longer renders as a table under GFM (verified with `pandoc`; §4 n6). That is a formatting defect only
(no value, pin, record, status or citation is affected) and therefore a MINOR under this review's taxonomy, but
condition **C1 is mandatory before the census is committed as the final U4 record**. The other nine MINORs
(§3, §4) may remain as recorded conditions per the coordinator's rule; the full list is C2–C10.

---

## 1. M1 closure verification against the committed record (HEAD `92ed9bb9`)

### 1.1 Census claims about the AR smoke — all verified against the committed result dir

| census claim | committed evidence | match |
|---|---|---|
| smoke **attempted 20 Nov**, launched **22:35:48Z** on card 5 `GPU-5357dc5f…`, **verified idle** | `launch_ar_cond7a_attempt1.log` `start=2026-11-20T22:35:48Z`; `gpu/gpu_qualify.txt` 22:35:51Z: card 5 `48,427 MiB` free, `0 %`, `other_compute_apps_on_card=0`; `gpu_before.txt` 5 MiB used | ✅ |
| co-tenant **zihaozhao, 9 processes, 42,570 MiB (≈41.6 GiB)**, started **~3 min later** | `failure_time_census.txt` (22:54:14Z): exactly 9 zihaozhao pids on card 5, `3×4566 + 3×6862 + 3×2762 = 42,570 MiB = 41.6 GiB`; etimes 15:07–15:32 → started ≈22:38:42–22:39:07, i.e. ≈2 min 54 s to ≈3 min 19 s after the 22:35:48Z launch | ✅ |
| baseline **died with `CUDA out of memory`** | `U2_ISO_AR_COND7A_RESULT_20261120.md` §4 (`torch.OutOfMemoryError … 157.00 MiB free`); `s000_baseline` outcome `divergent / nonzero_exit / value null`, `returncode 1`, `timed_out:false` | ✅ |
| **STOPPED at 22:54:22Z** (`DONE_STOP`, rc 137) | `DONE` = `DONE_STOP 2026-11-20T22:54:22Z`; `RESULT_STATUS.txt` `status=STOP`, `systemd_run_rc=137`, `end_utc=2026-11-20T22:54:22Z` | ✅ |
| only **baseline record + refused s001** exist | `summary.json`: exactly 2 records — `s000_baseline` (`executed:true`) and `s001` (`executed:false`, refusal `scope_violation` on frozen `run_fixed_budget.py`); `s002` partial with no record | ✅ |
| no **`CHECKLIST_E_PASSED`** | `smoke_stdout_extract.txt` = **0 bytes**; `RESULT_STATUS.txt` `checklist_e_passed=0`, "STOP: CHECKLIST_E_PASSED autoresearch_fixedtokens missing" | ✅ |
| **transfer slowdown was not measured** | `slowdown.json` `B2_seconds:null`; only the failed baseline `748.79 s`; the report §5 and `slowdown.json` itself label the `1.057 s` per-request surrogate **invalid as a transfer measurement**; `smoke_slowdown_vs_17nov_wall` is a wall-time ratio, not the transfer measurement | ✅ |
| **external co-tenancy failure, not a code failure; no CUDA IPC error** | `verify_full.json` `no_cuda_ipc_error:true`; report §4 AST scan NONE; no CUDA-IPC marker in the run log | ✅ |
| isolation **`effective:true` / `waivers {}` / `exceptions []`**, private `/dev/shm` | `s000_baseline/run_record.json` `isolation.effective:true`, `waivers {}`, `exceptions []`, `log_intact:true`, `worker_sandbox.shared_dev_shm:false`, `cgroup.kill.empty_after:true` (11 processes before), result channel empty (`e3b0c44…`) | ✅ |
| training completed **500 steps, peak VRAM 1,980.1 MB** | report §4 `500/500 steps`, `AR_TOKENS consumed=32768000`, `AR_INFO peak_vram_mb=1980.1`; `slowdown.json` `peak_vram_mb_worker:1980.1` | ✅ |
| frozen pin **`147f0d35…` (committed) / `069e987a…` (deployed)** | `pins.txt`, `prep/pins_committed.txt`, `prep/pins_deployed.txt`; `run_record.frozen_pin_sha256 = 069e987a…` | ✅ |
| **one smoke consumed; no retry** | exactly one result dir and one launch attempt (`launch_ar_cond7a_attempt1.log`/`launch_attempt1.log`); `RESULT_STATUS.txt` "(timeout/OOM/failure; no retry)"; report §6.5 "No retry was performed"; census `:90` now states no retry + fresh authorisation + guaranteed-idle card | ✅ |
| **isolated U2 not run; 17 Nov un-isolated U2 passed B1 67.901 s; joins only after clean smoke + U2** | census `:91-92` ("The isolated autoresearch U2 is **not run** (the 17 Nov un-isolated U2 passed B1 67.901 s); the row joins G.1b/G.4 only after a clean smoke + U2 review"); report §5 reference `B1 67.901 s`; `slowdown.json.reference_17nov`; `PLAN:1330` G3-EARLY + `R1-TRACKG-AR-COND7` (`:1317`) | ✅ |
| **report sha `bcb74efc…`, SHA256SUMS `231d388e…`** | `shasum -a 256` of both files (working tree and HEAD blobs) **both match** | ✅ |
| gate capture `clear_finished`, paper_a_processes [] | `gate/gate_20261120T223548Z.json`: `verdict:clear_finished`, `paper_a_live_waiting_for_card:false`, `evidence.gpu.paper_a_processes:[]` | ✅ |
| branch **pushed**, reviewed `13786d1f`, code review `261a03e9` ACCEPTED (1 report-only MAJOR + 6 MINOR), report tip `7330338`, report sha `370782ab` | harness worktree `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120` = `7330338` (and local branch = `7330338`); code review `261a03e9…` "ACCEPTED … 0 BLOCKING, 1 MAJOR, 6 MINOR", reviewed HEAD `13786d1f`; code unit `370782ab…` at tip `7330338` — all committed at HEAD `92ed9bb9` | ✅ |
| co-tenant size **`42,570 MiB (≈41.6 GiB)`** | corrected from the R4 problem: `42,570 MiB = 41.57 GiB` ✅ (the committed AR report itself still labels it "≈42.6 GiB"; that is an inherited slip in the AR report, not in the census) | ✅ |
| result-record path **`ar_cond7a_smoke_20261120T223548Z/`** | repo-relative path exists under the census base path; the previous malformed `u2_iso_.../` prefix is gone | ✅ |

### 1.2 The old contradictory sentence is gone

`:58-60` now reads:

> "**autoresearch (1 node):** not in this census; condition-7 option-A code unit accepted, but the one isolated
> Ada smoke was attempted and STOPPED (external co-tenant CUDA OOM; slowdown not measured; no retry). It joins
> after a fresh clean isolated smoke + U2 review."

This is the R4-C1-required rewrite in substance: it no longer asserts the smoke is pending/waiting for a GPU,
and it now states attempted/STOPPED/external co-tenant OOM/slowdown-not-measured/no-retry/join condition. A
`grep -Ei 'pending|not yet|await|will '` over the census finds **no** remaining AR status claim of the old kind
(the only hits are the legitimate "idle GPU (verified idle)", HousePrice's CPU-idle STOP disclosure, and the
"guaranteed-idle card" condition). The header (`:4-6`) says "autoresearch joins after a clean isolated smoke +
U2" and G.1b/G.4 no longer wait for the report, which matches `PLAN:1330` (the six nodes
mlab_cifar10/mlab_imdb/mlab_obgn_arxiv/mlgym_cifar10/mlgym_fmnist/mlgym_breakout_minatar are set now;
HousePrice and autoresearch join when their U2 passes, with the AR smoke precondition from `:1317`).

The funnel bullet does not repeat the exact launch/stop timestamps, the "CHECKLIST_E_PASSED not reached" clause,
the isolated-U2-not-run / 17 Nov facts, or the "fresh authorisation" phrase; those are correctly stated in the
Blocked section (`:82-92`, `:91`). That is a summary/indexing choice, not a contradiction — the census as a
document states every required fact once, in the right status section. **M1 is CLOSED.**

### 1.3 Readiness / G3-EARLY accuracy

- `docs/r1/PLAN.md:1330` (HEAD, `origin/main df58bcd5`, and commit `94db94bb` — **not** `de3de54f`, which has
  1,317 lines): "T1 nodes are set now to the six census nodes that passed isolated U2: mlab_cifar10, mlab_imdb,
  mlab_ogbn_arxiv, mlgym_cifar10, mlgym_fmnist, mlgym_breakout_minatar. autoresearch_fixedtokens and
  mlgym_houseprice join as soon as their U2 passes. G.1b and G.4 start on these six now, without waiting for
  the U4 census report".
- Census `:4-6` and `:97-98` match that (six now; HousePrice joins now — its U2 passed and is accepted; AR joins
  after its option-A smoke + U2; the census does not block G.1b/G.4 and is not evidence). **Accurate.**
- **Citation residual:** the Authority-citation section (`:103-104`) says "`R1-TRACKG-G0-GO` (main `de3de54f`
  PLAN:1258), … `R1-TRACKG-G3-EARLY` (:1330)" — `:1330` does **not** exist at `de3de54f`; the G3-EARLY row must
  be attributed to `94db94bb` (or `origin/main df58bcd5`, PLAN 1,337 lines). The AR-COND7 row (`:1317`, main
  `df58bcd5`) is not attributed either. See m6/C6.

---

## 2. Measured rows — independent recomputation (all exact)

Mechanical cell counts: main table **header and all 7 data rows have 15 cells** (`:12`, `:14-20`), **but the
delimiter row (`:13`) has only 14 cells** → the table is not a valid GFM table (see n6). Run-level table:
header+delimiter 5 cells (`:24-25`) but all 7 data rows have **6 cells** (the main table's licence/availability
strings were appended to the run-level rows without a header cell; see n6). Readable raw, but malformed.

| node | B1 s / value | B2 s / value | sealed | 3×B1 | VRAM bound (MiB) | max RSS kB | disk before→after (B) | committed / deployed pin | manifest | UUID (card) / cpus | gate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 / 0.5152 | 11.846 / 0.5152 | 0.5015 | 36.891 | 836 | 1,402,612 | 74,632,835,072→74,630,283,264 | `1f047ad7` / `a459b3d8` | `43fdf860` | aa340032 (1) / 0-7 | clear |
| mlab_imdb | 64.142 / 0.9048 | 64.133 / 0.9048 | 0.89924 | 192.426 | 11,292 | 1,659,008 | 74,629,115,904→74,609,201,152 | `4b1019a6` / `c169a6b8` | `a87254e1` | f439cca8 (2) / 0-7 | clear |
| mlab_ogbn_arxiv | 5.651 / 0.275982 | 5.665 / 0.275982 | 0.238442 | 16.953 | 4,544 | 1,256,776 | 74,610,388,992→74,605,633,536 | `bd71fdf4` / `5ff5824a` | `91312162` | 3b36edea (6) / 0-7 | clear |
| mlgym_cifar10 | 31.731 / 0.491 | 31.244 / 0.491 | 0.4926 | 95.193 | 982 | 1,493,864 | 74,604,687,360→74,597,408,768 | `2d7e533b` / `817c9034` | `c0ef1168` | 3719bd35 (7) / 8-15 | clear |
| mlgym_fmnist | 34.376 / 0.861667 | 28.868 / 0.861667 | 0.8515 | 103.128 | 912 | 1,213,024 | 74,596,868,096→74,548,490,240 | `eb60107e` / `ef804338` | `8d28287b` | f439cca8 (2) / 8-15 | clear |
| mlgym_breakout_minatar | 61.248 / 22.486719 | 61.781 / 22.486719 | 22.885938 (`test_return`) | 183.744 | 634 | 1,262,488 | 75,439,427,584→75,401,625,600 | `cec562e6` / `cec562e6` | none (simulated) | 3b36edea (6) / 8-15 | clear |
| mlgym_houseprice | 5.059 / 23344.767385 | 4.876 / 23344.767385 | 30295.671017 (`test_rmse`) | 15.177 | n/a (CPU; max RSS 599,392 kB) | 599,392 | 70,644,187,136→70,795,374,592 | `88d359f2` / `4cbbc5d6` | `73ee5597` | CPU 79,78,77,76,59,42,34,28 | clear |

Verification basis (all read-only, recomputed file by file):

- Every B1 value/elapsed equals `runs/runs_smoke/s000_baseline/run_record.json`; every B2 value/elapsed equals
  `runs/runs_edits/B2/run_record.json`; every sealed value equals `run_record.sealed`; `3×B1` is exactly
  3 × B1 elapsed; max RSS equals each `time_v.txt` "Maximum resident set size (kbytes)"; the VRAM bound equals
  each `sampler/sampler_max.json` `max_per_sample_sum_mib` (HousePrice has no sampler → the CPU/RAM cell);
  disks equal the `/dev/md0p3` `Available` bytes in `disk_before.txt`/`disk_after.txt`; committed pins equal
  `pins.txt` `committed_file_pin[<node>]`; deployed pins equal the run-record `frozen_pin_sha256`
  (`a459b3d8`/`c169a6b8`/`5ff5824a`/`817c9034`/`ef804338`/`cec562e6`/`4cbbc5d6`); manifests equal
  `data_manifest.txt` `data_manifest_sha256` (Breakout correctly `none (simulated)`); GPU UUIDs and cpusets equal
  the record's `limits.gpu_uuids` / `limits.cpu_list` (including HousePrice's CPU list
  `[79,78,77,76,59,42,34,28]`); every gate JSON is `clear_finished`, `paper_a_live_waiting_for_card:false`,
  `paper_a_processes []`; every node has **9 records = 8 executed + 1 refused `s001`** (frozen-diff/scope
  violation); every `summary.json` is `gate_ok:true`, `issues:[]`, all `synthetic_in_*:false`; every dir has a
  committed `unit/` and the expected `gpu/` (or `cpu/`) before/mid/after captures and `cgroup_probe.txt`
  (`memory.max=8589934592`, `memory.swap.max=0`).
- `shasum -a 256 -c SHA256SUMS` **rc 0 in all seven dirs** (428 / 427 / 426 / 426 / 426 / 1,117 / 447 entries,
  0 failures).
- Kit tips match the records: MLAB `fb6e7d73ddd2…` and MLGym `f07875de79a5…`, both contain the accepted
  isolation core fix `5403392e` (verified in the harness worktree); env claims verified (`envs/torch312`,
  Python 3.12.16, torch 2.6.0+cu124 for the five torch nodes + HousePrice; `envs/jax312` jax 0.4.35 CUDA-12,
  `nvidia-cuda-nvcc-cu12` absent, for Breakout).
- Attempt-1 pre-launch refusals are present in the records (`attempt1_prelaunch_cpu_idle_stop` for HousePrice —
  "selected CPU set mean idle 70.6% < 80%; no smoke launched"; `attempt1_prelaunch_gate_stop` for Breakout —
  "Paper A gate three-check not clear … unidentified_apps: 1; no smoke launched"). The census's "no node was
  dropped / every attempted row that failed pre-launch is disclosed" claim holds.
- AR `SHA256SUMS` verifies **1,800/1,800 rc 0 in the working tree**, but 17 hashed files are not in HEAD
  (1,789 files): see n5/C10.

**No fabricated row, no overclaimed number, pin, manifest, gate or record.** The table-format defect (n6) is
structural only.

---

## 3. R4 MINOR closure matrix

| round-4 item | status | evidence in the current object |
|---|---|---|
| m1 metric-key labelling | **partial** | sealed-test cells now carry the metric key for all seven rows (5 × `test_accuracy`, `test_return`, `test_rmse`) ✅; **B2 metric cells of Breakout and HousePrice are still bare** (`:19-20`: `22.486719`, `23344.767385` with no `val_return`/`val_rmse`; their B1 cells are labelled). |
| m2 HousePrice bound / disk units / stale wording | **partial** | `:20` whole-smoke bound is now `n/a (CPU; max RSS 599,392 kB)` with an explicit CPU/RAM label and cross-reference ✅; disk cells (`:26-32`) still carry byte values with no unit; `:34-36` still says "disk before/after and per-run hashes are in the record captures" although the run-level table carries disk before/after (stale/redundant wording). |
| m3 "U2 not run" opener | closed at R4 | `:77-92` correct. |
| m4 fix-review verdict + duplicate filename | **partial** | `:68-69` now cites `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` **with "verdict ACCEPTED"** ✅; the filename is still listed **twice** (`:68-69`: "…fix review `…REVIEW_20261119.md` sha `c8e468c7…`, verdict ACCEPTED; `HARNESS_ISOLATION_FIX_REVIEW_20261119.md`"). Also condition 6 PASS / condition 7 blocked is stated ✅. |
| m5 per-node licence/availability | **partial** | A 15th `licence/availability` column was added to the main table ✅, but its content is not the U1 §7 per-node licence/availability table: MLAgentBench code licence MIT is absent; CIFAR-10 "unknown", IMDb `license: other`, ogbn-arxiv ODC-BY, Fashion-MNIST MIT are compressed into "generic citation"; only MLGym CC BY-NC 4.0 and gymnax Apache-2.0 appear; no explicit availability status per node (U1 §7 gives public/HTTP 200/container/data-present). U1 §8 says it "supplies the U4 census's licence/availability columns". |
| m6 citations/shas | **open** | `:103-109` still gives acceptances by filename only: kit-update report current sha `fe232e2b…` vs **reviewed `3c3ae74a…`** (review `d8c68f9f…`, C-K1–C-K5) not stated; per-node unit reviews (`217822fe…` Breakout, `36774ed5…`/`81580eec…` HousePrice R1/R2, and the five-node review chain `0613a0c0…` R1, `4afacb5d…` R2, `99daf16d…` R3-ACCEPTED) absent; "**six isolated U2 result reviews**" is wrong — there are **three result reviews covering six nodes** (`965dc993…` five nodes, `d4cdd9bb…`, `b2c463a7…`), and the census lists only two; U4 basis docs (`903fc8a5…`, `5cd2a0cb…`) and the U1 audit (`70d54b71…`) absent; `R1-TRACKG-G3-EARLY (:1330)` not attributed to `94db94bb`/`origin/main df58bcd5` (and `:1330` does not exist at the cited `de3de54f`); AR-COND7 (`:1317`, main `df58bcd5`) not attributed; the AR code review's "0 BLOCKING" and its conditions C1–C6 not stated. |
| m7 imdb verbatim disclosure | **open** | `:51-54` still paraphrases ("written by us … DistilBERT-base-uncased … MLAgentBench ships only a skeleton and no upstream baseline") and still closes with the self-referential "the census/paper appendix must carry this disclosure"; the mandated sentence at `TRACKG_PORT_ISOLATION_20261117.md:98-99` — "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton for this task." — is not reproduced verbatim, and the self-referential clause reads as an open obligation inside the appendix. |
| m8 "whole-smoke CPU/RAM aggregates labelled" | **open** | `:41` still says "whole-smoke CPU/RAM aggregates labelled"; the census carries whole-smoke **max RSS** (RAM) and the VRAM upper bound only — no whole-smoke **CPU** aggregate (CPU time is only in the `time -v` captures/result mds). |
| m9 traceability / preserve reviewed sha | **open** | The census is still **untracked** and was rewritten **in place** again (`35d2c3e3…` → `4e050ad2…`, mtime 23:13:32Z, 52 s after the R4 review file's 23:12:40Z); the R4 object is not a git object and exists nowhere else in the workspace. Acceptance must bind to `4e050ad2…` and that revision must be committed/preserved; any further substantive revision needs a preserved copy + auditable delta (or a fresh review). |
| n1 co-tenant GiB conversion | **closed** | `:83` now `42,570 MiB (≈41.6 GiB)` — arithmetic correct (42,570 MiB = 41.57 GiB), matching `failure_time_census.txt` pids. (The committed AR report still carries the inherited "≈42.6 GiB" label; a separate AR-report correction note would close that, not a census issue.) |
| n2 corrected record path | **closed** | `:86` `Result record ar_cond7a_smoke_20261120T223548Z/` (repo-relative, no `u2_iso_...` prefix). |
| n3 stale HousePrice header parenthetical | **closed** | `:4-6` now "HousePrice joins now; autoresearch joins after a clean isolated smoke + U2". |
| n4 no-retry wording | **closed** | `:90` now "One smoke was consumed; **no retry was made and a new smoke needs fresh authorization**, and a fresh isolated smoke needs a guaranteed-idle card for the whole run" — matches report §6.5 and `RESULT_STATUS.txt`. |
| n5 SHA256SUMS vs committed file set | **open** | At HEAD `92ed9bb9` the AR `SHA256SUMS` lists 1,800 files but the HEAD tree has 1,789: 17 hashed files (logs, launch logs, run logs, `smoke_ledger.jsonl`, `__pycache__/*.pyc`) are absent from HEAD. They are present in the working tree and are now **staged in the index** (`git status` 17 × `A`) but not committed; the census states no caveat. A fresh checkout of HEAD cannot re-verify the committed SHA256SUMS (the working tree verifies 1,800/1,800 rc 0). |

---

## 4. Findings

### n6 — MINOR (new, formatting/rendering; release-blocking condition C1): the R5 edit broke both table structures

The revision added the licence/availability column to the main table's header (`:12`, 15 cells) and to every
data row (`:14-20`, 15 cells), but **not to the delimiter row**: `:13` is
`|---|---|---|---|---|---|---|---|---|---|---|---|---|---|` = **14 cells**. Under GFM the header and delimiter must have the
same number of cells; with 14 vs 15 the main table is not recognised. Verified: `pandoc … -f gfm -t html`
emits **one** `<table>` (the run-level one) and renders the entire seven-row main table as a literal `<p>| node |
suite | …` paragraph; `-f gfm -t latex` emits a single five-column `longtable` and no main table. Since this
table is the census's primary deliverable (and is destined for the paper appendix), the committed artifact
would not display its measured rows. The run-level table got a second defect from the same edit: its
header/delimiter have 5 cells (`:24-25`) while all seven body rows (`:26-32`) have **6** (the licence/availability
strings were appended to the run-level rows too). GFM ignores the excess body cells, so the run-level table still
renders, but the rows are inconsistent and the licence text is duplicated from the main table without a header.

No measured value, pin, manifest, gate, record, status or citation is affected — the text is correct and raw-
readable; this is a formatting regression introduced in the R5 revision (the R4 review recorded the main table as
14 cells per header/data row). Classified MINOR (not MAJOR) because no claim is false or unsupported; classified
**release-blocking** because C1 must be fixed before the census is committed/rendered.

### m1 — MINOR: B2 metric keys still missing for Breakout and HousePrice

`:19` B2 = `22.486719` (should be `22.486719 (val_return)`); `:20` B2 = `23344.767385` (should be
`23344.767385 (val_rmse)`). Sealed keys and B1 keys are now complete. Values verified correct; C2.

### m2 — MINOR (residual): disk units and stale disk wording

`:26-32` disk cells still carry raw bytes with no unit (add `B`, or convert and say `GB/GiB`); `:34-36` still
says "disk before/after and per-run hashes are in the record captures" though the run-level table now carries
disk before/after (keep the per-run-hashes part, drop/reword the disk part). The HousePrice RAM/VRAM bound cell
is fixed; C3.

### m4 — MINOR (residual): duplicated fix-review filename

`:68-69` cite `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…` with **verdict ACCEPTED**, but the same
filename appears twice (second occurrence at `:69` has no content). Remove the duplicate; C4.

### m5 — MINOR (residual): per-node licence/availability column content is not the U1 §7 data

The column exists but needs the per-node code licence / asset licence / availability status from
`U1_LICENCE_AVAILABILITY_20261117.md` §7 (MLAgentBench MIT; MLGym CC-BY-NC-4.0; CIFAR-10 unknown; IMDb
`license: other`; ogbn-arxiv ODC-BY; Fashion-MNIST MIT; gymnax/Gymnax-blines Apache-2.0; Kaggle terms; all
public/HTTP 200 or data-present per the U1 audit) — the current cells are "generic citation"/"data present"/
suite-level compression; C5.

### m6 — MINOR (open): authority/acceptance citations remain names-only and incomplete

As itemised in §3 m6: kit-update report current `fe232e2b…` vs reviewed `3c3ae74a…` (+ C-K1–C-K5, review
`d8c68f9f…`); per-node unit reviews and the `99daf16d…` chain; the three result reviews' shas and the wrong
"six … result reviews" count; U4 basis docs `903fc8a5…`/`5cd2a0cb…`; U1 audit `70d54b71…`; G3-EARLY attributed
to `94db94bb`/`origin/main df58bcd5` (not `de3de54f`); AR-COND7 `:1317`; the AR code review's "0 BLOCKING" and
C1–C6. C6.

### m7 — MINOR (open): imdb disclosure not the mandated verbatim sentence

Use the verbatim sentence from `TRACKG_PORT_ISOLATION_20261117.md:98-99` in the funnel/appendix and drop the
self-referential "the census/paper appendix must carry this disclosure" clause; C7.

### m8 — MINOR (open): "whole-smoke CPU/RAM aggregates labelled" overstates the content

`:41`. Only the whole-smoke max RSS (RAM) and the VRAM upper bound are carried; no whole-smoke CPU aggregate
exists in the census. Reword to "whole-smoke RAM (max RSS) and VRAM upper-bound numbers labelled" (or add the
CPU-time aggregate from the `time -v`/result captures); C8.

### m9 — MINOR (open, traceability): reviewed revision still not preserved; in-place rewrite again

Same class as R4 m9, repeated: untracked census rewritten in place (`35d2c3e3…` → `4e050ad2…`, 52 s after the
R4 review file), R4 object not preserved anywhere, so the R4→R5 delta could only be audited against R4's quoted
text + recomputation. Acceptance must bind to `4e050ad2…` and that revision must be committed/preserved; any
further substantive edit needs a preserved copy + auditable delta (C9).

### n5 — MINOR (open, commit integrity): committed AR SHA256SUMS does not correspond to the HEAD file set

1,800 hashed entries vs 1,789 HEAD files; 17 hashed evidence files (logs, launch logs, run logs,
`smoke_ledger.jsonl`, `__pycache__/*.pyc`) exist in the working tree and are **staged** (17 × `A`) but not
committed at HEAD `92ed9bb9`, so a fresh checkout of HEAD cannot re-verify the committed record for the AR smoke.
The census should either rely on the acceptance commit including those staged files, or state the caveat
(C10). (The seven U2 dirs do not have this problem: their SHA256SUMS verify rc 0 against the committed tree
locally, 0 failures.)

---

## 5. Conditions for acceptance (documentation only — no new run, no record/measurement edit)

- **C1 (n6; mandatory before the census is committed as the final U4 record).** Repair the table structure:
  make the main-table delimiter row 15 cells (matching the 15-cell header and all seven data rows), and remove
  the duplicated licence/availability text from the run-level data rows (restore 5-cell rows; do not add a
  licence column to the run-level table, since the main table already carries it). Re-run the mechanical check
  (header cells == delimiter cells == every row's cells for both tables) **and** the render check
  (`pandoc -f gfm` must produce two tables). Docs-only; no value changes. Per R4 m9 rules, preserve a copy of
  `4e050ad2…` and record the C1-only delta and the new sha; no fresh substantive review is needed for this
  mechanical repair, but any other text change does need one.
- **C2 (m1).** Label the B2 cells `22.486719 (val_return)` and `23344.767385 (val_rmse)`.
- **C3 (m2).** Add a unit to the disk before/after cells and reword the stale disk clause at `:34-36`.
- **C4 (m4).** Remove the duplicated `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` occurrence (keep the
  ACCEPTED/sha `c8e468c7…` cite and the condition 6 PASS / condition 7 blocked statement).
- **C5 (m5).** Complete the licence/availability column per U1 §7: per-node code licence, asset licence, and
  availability status (MLAgentBench MIT; MLGym CC-BY-NC-4.0; CIFAR-10 unknown; IMDb `license: other`;
  ogbn-arxiv ODC-BY; Fashion-MNIST MIT; gymnax-blines Apache-2.0; Kaggle competition terms; public/data-present).
- **C6 (m6).** Give shas and complete the citations as itemised: kit-update current-vs-reviewed sha + C-K1–C-K5;
  per-node unit reviews; the three result reviews and "three reviews covering six nodes" (not six reviews); U4
  basis docs; U1 audit; G3-EARLY attributed to `94db94bb`/`origin/main df58bcd5` (`:1330`, not `de3de54f`);
  AR-COND7 `:1317`; AR code-review "0 BLOCKING" + C1–C6.
- **C7 (m7).** Insert the verbatim mandated imdb sentence and drop the self-referential clause.
- **C8 (m8).** Reconcile the "whole-smoke CPU/RAM aggregates labelled" wording with what the census carries.
- **C9 (m9).** Bind acceptance to sha `4e050ad2…`, commit/preserve that revision (and the C1-repaired successor
  with its recorded delta); do not rewrite the census in place again without a preserved copy + auditable delta.
- **C10 (n5).** Commit the 17 staged hashed AR evidence files with the acceptance commit (then 1,800 hashed
  entries correspond to the committed tree and a fresh checkout can verify them), or state the SHA256SUMS
  caveat explicitly in the census. After committing, re-run `shasum -a 256 -c SHA256SUMS` from a fresh checkout.

C1 is the only condition that must precede the commit for the artifact to be usable; C2–C10 are documentation
corrections that the coordinator may carry as recorded conditions (the measured rows, pins, manifests, gates,
records and the AR status do not depend on them). Nothing in this review changes a measured number, pin,
manifest, gate capture, isolation record or AR status; the seven rows and the AR STOP are fully supported by the
committed records.

---

## 6. Acceptance binding / traceability

Acceptance is bound to the reviewed content
**`docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
`4e050ad22c63dde41af191a3adac678252f789da2dd56f2871755895716fa285`, 109 lines / 11,207 bytes,
mtime 2026-11-20T23:13:32Z**, currently **untracked at HEAD `92ed9bb9`**. The census must be committed (or
otherwise preserved with its sha recorded) as part of acceptance; the C1 repair is the only permitted
pre-commit edit and its delta must be recorded against `4e050ad2…` (with a preserved copy), because the R4
object (`35d2c3e3…`) was not preserved and the R4→R5 delta could only be checked by recomputation, not
byte-for-byte. Any further in-place revision after acceptance needs a fresh review or a preserved copy +
auditable delta.

---

## 7. Attestation

Read-only review. The only file written is this review (uncommitted/untracked); no smoke/U2/GPU/Ada/SSH/
HTCondor/deepthought/TASL action; no unit, result, capture, record, pin, manifest, gate, census or review was
edited; no commit/push/delete. Commands used (all read-only, 20/21 November 2026, Europe/Berlin): `shasum -a 256`
of the census, the review chain, the AR smoke report/`SHA256SUMS`/`DONE`/`RESULT_STATUS`/unit/review and the
cited U1/kit/fix documents; `shasum -a 256 -c SHA256SUMS` in the AR dir (1,800/1,800 rc 0) and in all seven U2
dirs (rc 0, 0 failures); `git rev-parse/show/log/ls-tree/ls-files/cat-file/status/merge-base` (worktree and the
sibling harness worktree, incl. `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120`); `stat`, `wc`, `ls`,
`find`, `grep`, `awk`, `sed`, `date -u`; Python `json` reads of the AR `gate`/`gpu`/`failure_time_census`/
`slowdown`/`summary`/`verify_full`/`pins`/`prep` captures and of all U2 `run_record.json` (56 executed + 7
refused `s001`), the seven `pins.txt`, `data_manifest.txt`, `time_v.txt`, `disk_before/after.txt`,
`sampler_max.json` and gate JSONs; independent recomputation of every B1/B2 elapsed and value, sealed value,
3×B1, max RSS, VRAM upper bound, disk before/after, pins, manifest, gate, GPU UUID and cpuset for all seven rows;
mechanical markdown cell counts of both tables (15/14/15; 5/5/6) and a `pandoc -f gfm -t html/latex` render
check to stdout. No live-host state is claimed beyond what the preserved records, captures and local git state
contain.
