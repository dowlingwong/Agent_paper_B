# Independent review — Track G G.0 U2 result `autoresearch_fixedtokens` under option A on TASL-2 (21 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-ar-result-reviewer`), delegated by the lead; no involvement in writing
the smoke, the U2 result, the U2 unit/review, the option-A code/kit change, the TASL-2 host check or any earlier
U2/AR record. **Read-only:** the only file written is this review. No run, GPU/U2/T1 job, census job, edit, commit,
push, deletion or HTCondor/deepthought action. Verification was done on the Mac worktree in place plus **read-only
`ssh -o BatchMode=yes`** inspections of TASL-2 (`portal_zhixu`) and TASL-7 (`tasl7`); the probes/smoke were not
re-run.

## Objects, hashes and authority

| object | value |
|---|---|
| **U2 result (under review)** `docs/r1/reports/trackg_g0_20261117/U2_ISO_AUTORESEARCH_RESULT_20261121.md` | sha256 **`ca3bcadd990ab66a73dafaf26378093af03bf62106578d635980bf168590581d`**, 3,893 B / 57 lines, **untracked** |
| Smoke result `TASL2_AR_COND7A_RESULT_20261121.md` | sha256 **`8814eecc1fb0f9ded4920adc15aa276a05c08e5a181a0a1ed4c5d564f088d0ad`**, 22,667 B / 288 lines |
| Smoke captures `TASL2_AR_COND7A_RESULT_20261121_captures/` | `SHA256SUMS` sha256 **`32f5009a347264bb1d820c420dedeaf0d2dd5fe8822516597f1bba53a3ca0aeb`**; **7,055 entries, 7,056 regular files, 17 symlinks**, all listed hashes **OK**, `sha256sum -c`/`shasum -a 256 -c` **rc 0** on both the Mac copy and TASL-2 (live) |
| Accepted U2 unit (current, text-amended) | sha256 **`b83d91597eaf665b942f4f02fd30f149da53f5f1cc0e6579d1e6711669734432`**, 74 lines / 6,374 B (committed `d65079af`) |
| Reviewed U2 unit (object of the unit review) | sha256 **`3bb015a1ece7c65ac04181f73e4ae84aa12a2d99187dfa82043817ee8c1513ec`**, 56 lines / 4,489 B (recorded in the unit review only) |
| U2 unit review `TRACKG_U2_ISO_AUTORESEARCH_UNIT_REVIEW_20261121.md` | sha256 `ef42276d1310e80e3f275ca10e059dcdff46d2384dc45e280fb846f98a34e76a`; **ACCEPTED — 0 BLOCKING, 2 MAJOR, 14 MINOR, C1–C8** |
| Accepted option-A code review / fixed code report | `261a03e9afb5921f6afdcc0979e83122d1f8cbaef85d6cf723c21ded8db66cae` / `370782abf2c14850c9b56f70789df51bee3e332ac37bcf7a82134366081df0a8` (both recomputed here) |
| TASL-2 host-check report / its review | report sha256 `0a1fa3a42dfaa28a2faf3c98fb1f80a7d0d2fc2c2f70447e1f6857c44befed7a` (369 lines, unchanged from the review's object); review `bfe9b2312d7483e54ea8692544d4cf434c093616d0c4abc2cc09a1db214e0efd`, **ACCEPTED — 0 BLOCKING, 1 MAJOR (report-only), 6 MINOR, C1–C4** |
| 17 Nov Ada un-isolated baseline / 20 Nov STOP / 21 Nov retry STOP | `a6ddfbd0c6c4d5d2905abe798495564a39ea91b87ebd623da5d6fe34a1b6ca8b` / `bcb74efc99f87bcd43a18b9deb56303c8a28774e0bd312e3ba78a72069096bdc` / `34bd3532cdfe3a90ae636417c3b70a95221d75ddcd59d1ae02518bc1630c1f7f` (all in `references/`) |
| Worktree / branch / origin | HEAD `ebe03cd5aa5a5e4ccc1e9b19108f52709bc3271d`, `origin/ops-tasl-20261116` = same commit (**no unpushed commit; the result is untracked, nothing pushed**); `origin/main` = `4aac5209` |

**Verdict: ACCEPTED — 0 BLOCKING, 1 MAJOR (report-only), 12 MINOR, conditional on C1–C5 below.** The one clean
isolated TASL-2 smoke is a genuine option-A measurement: every headline value reproduces from the run records,
logs and sampler/cgroup captures, and the live host/TASL-7 attestations hold. The MAJOR and the MINORs are
**record/label/condition-traceability** items; none changes a measured number, and none requires a re-run (a
re-run would violate the one-smoke/no-retry rule).

---

## 1. The one clean isolated smoke is the U2 measurement (no second run) — confirmed

- **One launch, one evidence root.** The smoke launched `2026-11-21T01:58:19Z` and ended `02:28:10Z`; the launcher
  log shows a single `systemd-run` scope (`tasl2_ar_smoke_cond7a.scope`, `systemd_run_rc=0`) and one
  `port_smoke_gpu` invocation. The `flock` on `~/r1_locks/gpu0.lock` was held `01:58:19Z–02:28:10Z`, **no lease-log
  write** (verified in captures and live).
- **9 records = 8 executed + refused `s001`.** `runs_smoke/{s000,s001,s002,s003}` + `runs_edits/{E1,E2,E3,E4,B2}`;
  `s001` is `executed:false`, refusal `scope_violation` ("`run_fixed_budget.py` is outside editable_paths / matches
  frozen_paths"); `s002` is `divergent` / `non_finite_loss` / token `nan`; the other 7 edit/baseline runs are `ok`.
  `B1 = s000_baseline`, `B2 = runs_edits/B2` (seeds split=train=8001, `run_budget {tokens 32768000}` in every record).
- **Live TASL-2 check:** only **one** AR evidence root (`/home/dowling/r1_engineering/tasl2_ar_cond7a_20261121`),
  exactly **9** `run_record.json` under its `runs/` (the two sub-roots above), no second AR run root, no
  leftover processes, no cgroup scopes, GPU back to `353 MiB / 0 % / 0 compute apps`. So there was **no second
  run and no retry**.
- **The preserved false STOP did not cause a re-run.** `RESULT_STATUS.initial_false_stop.txt` (`STOP: slowdown
  analysis rc=1`, same UTC stamp/lease window, `systemd_run_rc=0`, `checklist_e_passed=1`) and `DONE.initial_false_stop`
  are preserved; the final `RESULT_STATUS.txt` is PASS. The smoke log correctly shows the same single launch and
  `CHECKLIST_E_PASSED`. The slowdown-analysis script was re-run only (analysis, not smoke), `slowdown_rc=0`.
- **Sequence note:** the accepted unit (C8) describes "one fresh clean smoke, **then** the U2"; here the same single
  clean smoke is used as both the pre-U2 gate and the U2 raw-cost run. That is the arrangement in the author's
  task (the U2 result states "this U2 result is the same single clean smoke") and it is disclosed; see MAJOR-1/m4.
- **Checklist/verifier:** `CHECKLIST_E_PASSED autoresearch_fixedtokens`; COND7-aware `verify_full.json`
  `ok:true`, `issues:[]`, `ipc_hits:[]`, `executed_records:8`, `refused_s001:true`,
  `committed_pin 147f0d35…`, `deployed_pin ca049086…`, `sealed_key:null`, `smoke.checklist_e_passed:true`,
  `synthetic_marker:false`, `systemd_run_rc:"0"`, 9 JSON run lines.

## 2. Numbers reproduced independently (not taken from the report)

| quantity | reported | independently recomputed (source) |
|---|---|---|
| B1 `s000_baseline` | 218.951 s, `val_bpb 1.293937` | 218.951 s / 1.293937 (`run_record.json` outcome.value; `run.log` AR_INFO) |
| B2 repeat | 218.443 s, `val_bpb 1.293937` exact | 218.443 s / **1.293937 identical** |
| whole-smoke wall | 1,791.0 s (29:49) | lease window `01:58:19→02:28:10` = **1,791 s**; `/usr/bin/time -v` elapsed **1,789.26 s** = `29:49.26` |
| B1 vs 17 Nov Ada | 3.225×, +151.05 s | 218.951/67.901 = **3.2246 → 3.225**; diff **151.050 s** |
| whole smoke vs 17 Nov | 3.176×, +1,227 s | 1791/564 = **3.1755 → 3.176**; diff **1,227 s** |
| transfer surrogate | 0.2345 s/request | (218.951−67.901)/644 = **0.23455** (labelled a wall-clock surrogate; 644 = 640 val + 3 probe + 1 repeat, code report §8; predicted 0.15–0.25 s/request) |
| B1 `val_bpb` vs Ada 1.291068 | +0.002869, cross-host | 1.293937−1.291068 = **0.002869** |
| worker peak VRAM | baseline 1,980.1 MB; max 3,720.4 MB | AR_INFO per run: 1,980.1 (B1/B2/s002/s003/E1/E3), 1,948.1 (E4), **3,720.4 (E2)** |
| whole-smoke GPU sampler | 12,436 MiB upper bound; max single row 7,848 MiB | `sampler_max`: `max_per_sample_sum_mib 12436`, `max_single_row_mib 7848`, 3,506 rows / 1,777 samples / 1,786.7 s / 16 pids — correctly **labelled** upper bound, not a per-run peak |
| cgroup v2 memory | peak 5.17 GiB, OOM 0, swap 0 | `memory.peak 5,550,911,488 B` = **5.1698 GiB**; events `max/oom/oom_kill = 0`; `memory.swap.max 0`; cap `memory.max 8,589,934,592` (probe verified) |
| CPU/RAM whole smoke | user 1,529.05 s, sys 395.16 s, max RSS 3,204,520 kB | `time_v.txt` exactly those values |
| mean/min/max run | 223.547 / 216.768 / 255.916 s | recomputed from the 8 executed elapsed values = **223.5474 / 216.768 / 255.916** |
| executed working copies | runs total 158,854,790 B (151.5 MiB) | `executed_unit_bytes.txt` sum = **158,854,790 B** |

All values are present in the delivered bytes and are mutually consistent; **no fabricated or unreconstructed
value was found**. The cross-host comparison is correctly headed "vs the 17 Nov Ada un-isolated baseline" and the
bpb/VRAM rows explicitly say "cross-host … disclosed, not normalised".

## 3. Isolation / option A / kit / env / data — confirmed

- **Isolation on every one of the 8 executed records:** `effective:true`, `waivers {}`, `exceptions []`,
  `worker_sandbox.shared_dev_shm:false` (private `/dev/shm`), `log_intact:true`, result-channel sha present,
  `cgroup.kill` method with `empty_after:true`, `removed:true`, `euid 1008`, `ptrace_scope 1`, `nsdelegate:true`,
  GPU by UUID, `memory_method:"external"` with the exact 8 GiB/0 scope string, CPU list `[0..7]` (records + live
  re-read agree).
- **Option A = no CUDA IPC in the result path.** Independent AST scan (not grep) of the captured node files:
  `ar_worker.py`, `run_fixed_budget.py`, `ar_parent.py` contain **no calls** to `cuda_share`/`cuda_open`/
  `_share_cuda_`/`_new_shared_cuda`/`bind_cuda`; the transfer is `iso.SharedBuffer` CPU `memfd` (`ar_worker.py:144`,
  `run_fixed_budget.py:76`). `ar_isolated.py` keeps the `cuda_share`/`cuda_open` compatibility helpers and
  `torch.cuda.init()` is in `cuda_open`, exactly as disclosed ("helper unused by this node" — no call sites in the
  kit tree). No CUDA-IPC error marker in any run log; verifier `no_cuda_ipc_error:true`, `ipc_hits:[]`.
- **Kit/tip/pins:** live TASL-2 worktree HEAD **`7330338…`**, tracked-clean except the expected untracked
  `nodes/autoresearch_fixedtokens/data` link; `merge-base --is-ancestor` **yes** for accepted core `68cdd1a…` and
  accepted Ada fix `5403392e…`; `origin/mac-trackg-iso-ar-cond7a-20261120` = `7330338…`; base repo `897d83c8…` on
  `trackp-20261026`, clean. Frozen-file and spec hashes on TASL-2 match `kit.txt` exactly (`ar_isolated 3ba34c67…`,
  `ar_worker 65a4927c…`, `run_fixed_budget 58d80b52…`, `ar_parent cbef1d38…`, `ar_budget c76b5d85…`,
  `prepare 3063fe87…`, `requirements cbfb98e7…`, spec file `5bdce00a…`). Committed-file pin **`147f0d35…` (20
  entries)** and deployed TASL-2 run-record pin **`ca049086…` (21 entries, path-dependent data link)** are
  separately recorded and every record carries `ca049086…`; Ada's `069e987a…` is correctly not expected here.
- **Data:** `/home/dowling/r1_trackp/data/autoresearch_fixedtokens`, manifest **`ab7186d2…`** = expected (live
  re-read), 13 manifest files / 14 on disk / 1,009,004,449 B (963 M), HF revision `915333b4…`, `vocab_size=8192`,
  dir mode 555, manifest 444, node link created; `synthetic_key_present=False`.
- **Env:** separate `/home/dowling/r1_trackp/venvs/ar-cond7a`, Python **3.12.15**, torch **2.6.0+cu124** (live
  re-read), freeze **122 lines `11def6ad…`** = expected; base Track P venv unchanged (`50238e5a…`, 121 package
  lines; dir/site-packages mtimes Oct 25).
- **Host:** TASL-2, kernel `6.8.0-149-generic`, Ubuntu 22.04.5, 32 CPUs, `MemTotal 65,543,252 kB`, RTX 4090
  24,564 MiB, driver **535.309.01**, UUID **`GPU-4d623e76…`**, boot `86c613a9…` — live values match §2.1. The
  17 Nov reference is Ada/L40S (`67.901 s`, `5,211.3 MB`, `1.291068`), so the disclosed host difference is real.

## 4. Preservation / authority / scope — confirmed with gaps

- **Attempt-1 archive, lease log and lock (live, read-only):** TASL-2 copy
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027` mtime `2026-11-17 15:42:26 -0800`, `journal.jsonl` sha256
  `1e73e80f…`; `_attempt1_gpu_lease_log.jsonl` 55,726 B mtime `2026-11-17 15:42:35 -0800` (**not appended**);
  `~/r1_locks/gpu0.lock` mtime `2026-11-20 17:58:19 -0800` = the smoke's flock acquire. **TASL-7:** archive
  mtime `2026-10-27 06:35:30 -0700`, `journal.jsonl` sha256 `1e73e80f…` (unchanged); no AR evidence root on TASL-7;
  GPU idle. No deletion, no push: worktree branch == `origin` (`ebe03cd5`), the result/smoke files are untracked.
- **Host TASL-2 authority:** the reports consistently name the author-signed **`R1-TRACKG-AR-U2-TASL2`** task
  (host checks + one clean isolated smoke + measured slowdown + report); the TASL-2 host check is **ACCEPTED** for
  the AR option-A gate with **no waiver**, explicitly **not** a §3 item 7 CUDA-IPC pass (item 7 remains untested and
  option A does not use it). **Gap:** that authorizing row is **not in the committed `docs/r1/PLAN.md`** (worktree
  HEAD or `origin/main` `4aac5209`); it appears only in the reports (m3).
- **T1:** `R1-T1-HOST-H200` is on `origin/main` (line 1329) as stated; the U2 result is explicitly an
  **ENGINEERING_ONLY** U2 raw-cost row and claims no evidence/no T1 label (but see m12 for the missing explicit
  no-evidence/no-noise statement).
- **Prior sessions correctly characterised:** the 20 Nov Ada attempt was a co-tenant CUDA OOM STOP with 1 executed
  record + refused `s001` and **no `CHECKLIST_E_PASSED`**; the 21 Nov retry session aborted both attempts on external
  contention with **0 run records**. Neither is a U2 measurement.

## 5. Unit-condition compliance (C1–C8, and the unit review's C1–C6)

| condition | state |
|---|---|
| C1 pre-U2 gate | **mostly met** — code review C1–C3 closed (code report `370782ab…` records the Ada Linux/CPU selections: `tests/trackg` 9 failed/186 passed/19 skipped/19 deselected before==after vs `448f682`; `test_port_autoresearch.py` 11 passed/18 skipped; tip `7330338` contains the fix); a clean isolated smoke passes — but on **TASL-2**, substituting the Ada smoke the code review named, under the new author-signed task (noted in MAJOR-1) |
| C2 STOPs/no-retry/fresh-authorization | **met** — the STOP set and "one smoke only, no retry" are stated; none triggered; the 20 Nov STOP is recorded as external |
| C3 COND7-aware verifier / stale-text note | **met** — `verify_ar_cond7a.py` (sha `8c4676a9…`) used, `ok:true, issues:[]`; the stale kit-update verifier rule is explained §7.3 |
| C4 ≥40 GiB floor + probe mismatch | **NOT literally met / not disclosed** — the launcher used a **20,000 MiB** free-VRAM floor (`gpu/gpu_qualify.txt`) on a 24,564 MiB card (23,830 MiB free at launch); the unit's 40 GiB floor is unattainable on this GPU and the substitution is absent from the deviations (m4). The probe half is met: `memory.max=8589934592`, `memory.swap.max=0`, cgroup.kill exposed |
| C5 exact B2 / mandatory 1 s sampler / result fields | **met except parent peak** — B2 `val_bpb` exactly equals B1; the mandatory 1 s compute-app sampler with upper-bound label is present; **`AR_INFO parent_peak_vram_mb=6560.3` is not recorded in either report** (m5) |
| C6 slowdown method / licence / pins / worktree / reviewed-unit sha / amended copy | **NOT fully met** — slowdown surrogate method, pins, worktree and licence text are present, but the **reviewed unit sha `3bb015a1…` and the executed amended unit copy are neither recorded nor preserved**; the committed amended unit `b83d9159…` still names Host Ada / `envs/torch312` / the Ada data root / Paper A gate, none of which is what executed (MAJOR-1) |
| C7 citations / scope | **met** — authorities cited; no push, no deletion, no HTCondor/deepthought, no secrets |
| C8 execution rule | **mostly met** — one node, ENGINEERING_ONLY, no evidence/no T1; the unit's "smoke **then** U2" is collapsed to one run under the author's task (disclosed, not recorded as a deviation; m4/MAJOR-1) |

## 6. Findings

| # | severity | where | finding |
|---|---|---|---|
| **MAJOR-1** | **MAJOR (report/record-only)** | U2 result / captures vs unit review C6/m13, unit C8, unit C1/C4 | **The executed procedure is not tied to the accepted unit, and the TASL-2 adaptations are not preserved.** The unit review's C6/m13 requires recording the reviewed unit sha `3bb015a1…` and preserving the executed amended unit copy; neither appears anywhere in the U2 result or the 7,056-file bundle (`3bb015`/`b83d91` occur only in the unit review). The committed amended unit (`b83d9159…`, `d65079af`) still targets **Host Ada, `envs/torch312` (Py3.12.16), `/home/dowling/r1_trackg_20261117/data`, the Paper A gate and the ≥40 GiB floor**, while the run used **TASL-2, `ar-cond7a` (Py3.12.15), `/home/dowling/r1_trackp/data`, no Paper A gate and a 20,000 MiB floor**; the single smoke also replaces the unit's pre-U2 smoke + U2 sequence. The author-signed TASL-2 task authorises the host, and the smoke report documents the env/data, so this is a traceability/record defect, **not a wrong measurement**; it can be closed by a text addition (C1) with no re-run. |
| m1 | MINOR | U2 result `:45` | "The 3.2× slowdown … **is recorded in the census**" is not true at review time: `TRACKG_CENSUS_20261117.md` (worktree and `origin/main`) still carries the 17 Nov un-isolated Ada row **67.9 s / 5,211 MB / 1.291068**, and `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` says "**no U4 measured row or accepted number changes: autoresearch remains blocked** … the autoresearch row joins only after a clean smoke + U2 review". No census file contains 218.951/3.225×. Reword to "to be recorded", or land the census/U4 update with this acceptance. |
| m2 | MINOR | host-check chain | Host-check review conditions **C1–C4 were not applied**: the cited host-check report is byte-unchanged (`0a1fa3a4…`), and its C1 asked for the opening/C6 label correction *before it is cited as the host-condition record* (item 7 CUDA IPC is UNTESTED; no `cuda_share`/`cuda_open` node may start on its strength). The U2 documents themselves carry the correct caveat, so the terminal record is not misleading; apply C1–C4 before the host report is committed/cited further. |
| m3 | MINOR | U2 result `:5`, smoke report `:11` | The authorising task **`R1-TRACKG-AR-U2-TASL2` row/delegation text is not in the committed PLAN** (worktree or `origin/main` `4aac5209`); host-check review m4/C3 already required recording it. The result discloses "starts now; reaches main after the sweep-2 launch", but the row text/lead delegation should be preserved in the record trail. |
| m4 | MINOR | unit C4 vs `gpu/gpu_qualify.txt` | The accepted C4 requires the qualification/watcher floor to be **40 GiB**; the launcher used **`floor_mib=20000`** (23,830 MiB free at launch on a 24,564 MiB card) and neither report lists this as a deviation (only the indirect "4090 vs L40S" note). The substitute (maximum-possible free VRAM, exclusive `flock`, 0 co-tenants, 12,436 MiB whole-smoke upper bound) is reasonable, but the floor change must be disclosed. |
| m5 | MINOR | smoke report §4 | Parent peak VRAM is not recorded: `s000_baseline/run.log` has **`AR_INFO parent_peak_vram_mb=6560.3`**; the reports give only worker peak 1,980.1 MB and the whole-smoke sampler upper bound. Unit C5/m12 asks for the worker **and** parent peak. |
| m6 | MINOR | smoke report `:127`; `scripts/slowdown_tasl2.py` | "median 218.951 s" is **not the median**: the sorted 8 executed values give arithmetic median 218.7935 s; 218.951 is `vals[len(vals)//2]` (upper middle). Label it "upper median" or compute `statistics.median`; no material effect. |
| m7 | MINOR | smoke report `:174` | "16.6 KB (`s001`, refused)" is wrong: `executed_unit_bytes.txt` gives **166,300 B ≈ 162 KiB** (~0.16 MB). Factor-10 conversion error. |
| m8 | MINOR | smoke report `:247` | Bundle byte total **161,531,825 B** is not reproducible from the delivered bundle: content bytes sum to **152,751,278 B** (identical on Mac and live TASL-2; all 7,055 SHA256 entries verify), and live `du -sb` is **161,534,003 B** (apparent size incl. 2,128 directories). Cite content bytes or label it apparent size; "7,056 files / 170 MiB du" is verified. |
| m9 | MINOR | smoke report §7.2 | The false-STOP traceback is **not** preserved where claimed: `slowdown.stderr.txt` is **0 B**; only `RESULT_STATUS.initial_false_stop.txt`/`DONE.initial_false_stop` evidence the false STOP. Add the original error text or reword the "(+ `slowdown.stderr.txt`)" parenthetical. |
| m10 | MINOR | U2 result `:39` | "wall **1,791.0 s (29:49)**" conflates the lease-window wall (1,791.0 s = 01:58:19→02:28:10) with `/usr/bin/time -v` elapsed **1,789.26 s** (`29:49.26`). The smoke report states both correctly; fix the U2 shorthand (3.176× is computed from 1,791/564). |
| m11 | MINOR | U2 result `:45` | "The 3.2× slowdown **is the measured option-A cost**" attributes the whole ratio to option A, but it is a **cross-host composite** (option-A CPU transport **plus** 4090/TASL-2 vs L40S/Ada; bpb/VRAM not normalised). The disclosure exists (§7.4 and the table's "vs 17 Nov Ada" heading), but where the single 3.2× headline is used — especially for the census row — label it "measured cross-host cost (option A + host change)". |
| m12 | MINOR | U2 result header; smoke report §10 | The explicit **no-evidence / no noise floor / no D21–D28 / no T1 label** statement required by the unit's result fields is absent (only "ENGINEERING_ONLY U2 census row" and "T1 labels run on H200" are stated; the 17 Nov precedent carries the full statement). Add it. |

**BLOCKING: none.** No fabricated value, wrong kit/tip/pin/data/env, ineffective isolation, CUDA-IPC use, co-tenant,
OOM, timeout, second run, deletion, push or unauthorised host/T1 action was found.

## 7. Conditions (text/record only; **do not re-run the smoke**)

- **C1 (MAJOR-1 — executed-unit record).** Add to the U2 result (and captures) a short executed-unit record:
  reviewed-unit sha `3bb015a1…` (56 lines) and amended-unit sha `b83d9159…` (74 lines); the TASL-2 adaptations
  (host, `ar-cond7a` Py3.12.15/freeze `11def6ad…`, data root `/home/dowling/r1_trackp/data` with unchanged
  manifest `ab7186d2…`, no Paper A gate, 20,000 MiB qualifier floor, and that the single clean smoke serves as both
  pre-U2 gate and U2 run), citing the author-signed `R1-TRACKG-AR-U2-TASL2`; or land a reviewed TASL-2 amendment
  of the unit. No re-run.
- **C2 (m1 — census).** Reword the "is recorded in the census" claim; when this acceptance is integrated, land the
  census/U4 addendum update recording the TASL-2 option-A row (B1 218.951 s, `val_bpb 1.293937`, B2 218.443 s exact,
  wall 1,791 s, 3.225× B1 / 3.176× smoke, worker peak 1,980.1 MB, cgroup peak 5.17 GiB, 12,436 MiB upper bound,
  committed pin `147f0d35…`), replacing the 17 Nov un-isolated 67.9 s row.
- **C3 (m2, m3 — host-check/authority records).** Apply host-check review C1–C4 to the TASL-2 host-check report
  before committing/citing it further (its C1 gate-scope correction; item 7 UNTESTED; no CUDA-IPC node), and
  record the `R1-TRACKG-AR-U2-TASL2`/delegation text in the record trail.
- **C4 (m4–m12 — report accuracy).** Disclose the 20,000 MiB floor substitution; add the parent peak
  `6,560.3 MB`; fix the median label, the `s001` "16.6 KB", the bundle-byte basis, the false-STOP stderr wording,
  the 1,791.0 s/29:49 shorthand; qualify the 3.2× label as cross-host (option A + 4090 vs L40S); add the explicit
  no-evidence/no-noise/no-D21–D28/no-T1 statement.
- **C5 (verification integrity).** Keep the one-smoke/no-retry rule: no condition here requires a re-run. If any
  cited report text changes, its sha changes and the U2 result must cite the new sha (the current pair is
  `8814eecc…` / captures `32f5009a…`). This review's acceptance lapses if the TASL-2 row is cited as census/valid
  T1 evidence or if option A is claimed to include CUDA IPC.

## 8. What was and was not done (read-only attestation)

- **Written:** only this review file (untracked; no commit, no push, no deletion).
- **Mac (read-only, in place):** `git rev-parse/status/log/show origin/main:docs/r1/PLAN.md`; `shasum -a 256` of
  the U2 result, smoke result, captures `SHA256SUMS`, unit (current), unit review, code review, code report,
  host-check report/review and all `references/`; `shasum -a 256 -c SHA256SUMS` (**7,055/7,055 OK, rc 0**); parsed
  all 9 `run_record.json`, `run.log`, `record_hashes.txt`, `verify_full.json`, `facts.json`, `slowdown.json`,
  `isolation_runs.txt`, `pins*.txt`, `data_manifest.txt`, `env*.txt`, `kit.txt`, `host*.txt`, `time_v.txt`,
  `disk_*.txt`, `sampler/*`, `gpu/*`, `lease_attestation.txt`, `final_state.txt`, `RESULT_STATUS*`, `DONE*`,
  `scripts/*` (incl. AST scan of the captured frozen files; slow-down/censor analysis); recomputed every number in
  §2; checked the census/U4 addendum, PLAN rows `R1-TRACKG-AR-COND7`/`R1-T1-HOST-H200`, git push status.
- **TASL-2 / TASL-7 (`ssh -o BatchMode=yes`, read-only):** single AR evidence root and 9 run records; host facts
  (kernel/driver/GPU-UUID/RAM/CPUs); kit worktree HEAD `7330338…` + `status`/`merge-base`/origin branch; base repo
  `897d83c8…` clean; frozen-file/spec shas; data manifest; `SHA256SUMS` sha and `sha256sum -c` (**rc 0**);
  `nvidia-smi` state (idle, 0 compute apps); scopes/processes empty; attempt-1 archive/journal/lease-log/lock
  stats; TASL-7 archive/journal and absence of AR evidence/GPU load.
- **Not done:** no run, probe, smoke, U2/T1/noise job, census job, GPU workload, kit/U2 file edit, commit, push,
  deletion/move, HTCondor/deepthought action, or secret/credential read. No TASL-7/HTCondor state was modified.

**Verdict: ACCEPTED — 0 BLOCKING, 1 MAJOR (report-only), 12 MINOR, conditional on C1–C5.** The TASL-2
option-A U2 measurement is genuine, one-smoke/no-retry, isolated (`effective:true`, no waivers, no CUDA IPC) and
its numbers are independently reproduced; acceptance does not extend to CUDA IPC, to T1/evidence use, to a second
run, or to any other node.
