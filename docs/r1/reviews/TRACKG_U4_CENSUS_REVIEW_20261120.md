# Independent review — Track G U4 census (`TRACKG_U4_CENSUS_20261120.md`) — 20 November 2026

**Reviewer role.** Fresh, independent, read-only reviewer (`u4-census-reviewer`), delegated by the coordinator;
no involvement in the seven U2 units/results, the kit update, the isolation fix, the autoresearch option-A code
unit or the census. Read-only: the only file written is this review (uncommitted). No smoke/U2/GPU run, no
record edit, no unit edit, no commit/push/delete, no HTCondor/deepthought/TASL. No Ada SSH was used — this
review is a paper review against the preserved records, captures and review chain in this worktree.

**Object under review.** `docs/r1/reports/trackg_g0_20261117/TRACKG_U4_CENSUS_20261120.md`, SHA-256
**`7774a4651fe4f8213ffcbffad22eb83e4d06e2b4cfb5559c39179840287ed94e`**, 56 lines, uncommitted (untracked) at
worktree HEAD `30cadb81` (branch `ops-tasl-20261116`); it asks for independent review in its status line.

**Authority / inputs read.**
- PLAN at the worktree: `R1-TRACKG-G0-GO:1258` (U4 = "census report **and each suite's screening funnel**"),
  `R1-TRACKG-PORT-DECISIONS:1289` (items (2), (3), (4)), `R1-HARNESS-ISOLATION:1290`, `R1-TRACKG-LICENCES:1269`,
  `R1-TRACKG-AR-COND7:1317`, `R1-T1-HOST-H200:1329`, `R1-TRACKG-G3-EARLY:1330`, `R1-BX-D12:756`. The first
  three rows and `R1-TRACKG-LICENCES` are at `de3de54f`; `R1-TRACKG-AR-COND7`, `R1-T1-HOST-H200` and
  `R1-TRACKG-G3-EARLY` are at `94db94bb` (verified with `git show <rev>:docs/r1/PLAN.md`).
- G.0 census/U4 basis `docs/r1/reports/TRACKG_G0_ADA_CENSUS_20261116.md` §2/§5 (`:31-33`, `:80-83`): raw cost =
  run time, peak VRAM, **CPU/RAM**; U4 = per-candidate rows, **per-suite funnel**, raw records, "functional
  qualification", non-qualifiers to the R1-BX-D12 appendix.
- U1 `docs/r1/reports/trackg_g0_20261117/U1_LICENCE_AVAILABILITY_20261117.md`:264 and §8 (U1 "supplies the U4
  census's licence/availability columns").
- Seven result directories `u2_iso_{mlab_cifar10,mlab_imdb,mlab_ogbn_arxiv,mlgym_cifar10,mlgym_fmnist,
  mlgym_breakout_minatar,mlgym_houseprice}_2026*Z/`, their result mds, `run_record.json` files, gates, cgroups,
  pins, manifests; accepted result reviews/corrections (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md`
  sha `965dc993…`; `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` sha `d4cdd9bb…`;
  `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` sha `b2c463a7…`; unit reviews R3 sha `99daf16d…`,
  HousePrice R2 sha `81580eec…`; corrections `U2_ISO_RECORD_CORRECTIONS_20261119.md`,
  `U2_ISO_BREAKOUT_RECORD_CORRECTIONS_20261119.md`, `U2_ISO_HOUSEPRICE_RECORD_CORRECTIONS_20261120.md`).
- Accepted kit update report `TRACKG_ISO_KIT_UPDATE_20261119.md` sha `fe232e2b…` and review sha `d8c68f9f…`;
  isolation fix report `HARNESS_ISOLATION_FIX_20261119.md` sha `0ff9a7f2…` and review sha `c8e468c7…`;
  host check `HARNESS_ISOLATION_HOST_CHECK_20261119.md` sha `6a700509…`; `JAX_ENV_FIX_20261119.md`.
- Autoresearch option-A code unit `TRACKG_AR_COND7A_CODE_UNIT_20261120.md` sha **`370782ab…`** (336 lines, in
  the sibling worktree `.claude-worktrees/harness_ar_cond7_20261120`, branch
  `mac-trackg-iso-ar-cond7a-20261120` @ **`7330338`**), and its independent review
  `docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha **`261a03e9…`** (403 lines).

---

## Verdict: NOT ACCEPTED — 0 fabricated rows; 1 BLOCKING, 1 MAJOR, 9 MINOR

The census's **measurements are correct**: every one of the seven rows' B1/B2 elapsed/value, sealed test,
3×B1 timeout, whole-smoke VRAM upper bound, card/cpuset, committed-file pin, data-manifest sha256 and record
path matches the preserved result records and run-record JSON (§1). The isolation/co-tenancy claims, the
ENGINEERING_ONLY/no-evidence/no-noise-floor/D21/D28/T1 labels, the HousePrice Kaggle sha256/md5 + `--from-file`
provenance, the kitchen/kit tips + isolation-fix references and the G3-EARLY readiness statements are also
accurate (§1). **No fabricated or overclaimed row was found.**

Acceptance fails on required content, not on numbers: (i) the U4 census carries **no census funnel / appendix**
and therefore omits the `R1-TRACKG-PORT-DECISIONS` (3)-mandated disclosure that the **mlab_imdb baseline was
written by us** (a hard condition of the authority row, repeated by the unit and result records); (ii) the U4
row fields are incomplete (G.0 raw cost requires CPU/RAM; the accepted results review requires the whole-smoke
CPU/RAM aggregate, both pins, the gate and disk records for the U4 row); and (iii) the blocked-list bullet on
autoresearch and several citations/naming fields are imprecise (MINOR). Conditions C1–C6 in §3 close all of
this without any new run or record edit.

---

## 1. What was verified correct (evidence)

### 1.1 The seven rows — every numeric/pin/manifest field matches the records

For each node I compared the census row (`TRACKG_U4_CENSUS_20261120.md:14-20`) with the node result md, the
9 `run_record.json` files (4 smoke + 5 edit runs) and the pins/manifests/probes in the result directory. All 7
rows agree; the reproduced values are:

| node | B1 elapsed / value | B2 elapsed / value | sealed | 3×B1 | whole-smoke upper bound | pin | manifest |
|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 s / 0.5152 | 11.846 s / 0.5152 | 0.5015 | 36.891 s | 836 MiB | `1f047ad7…` | `43fdf860…` |
| mlab_imdb | 64.142 s / 0.9048 | 64.133 s / 0.9048 | 0.89924 | 192.426 s | 11,292 MiB | `4b1019a6…` | `a87254e1…` |
| mlab_ogbn_arxiv | 5.651 s / 0.275982 | 5.665 s / 0.275982 | 0.238442 | 16.953 s | 4,544 MiB | `bd71fdf4…` | `91312162…` |
| mlgym_cifar10 | 31.731 s / 0.491 | 31.244 s / 0.491 | 0.4926 | 95.193 s | 982 MiB | `2d7e533b…` | `c0ef1168…` |
| mlgym_fmnist | 34.376 s / 0.861667 | 28.868 s / 0.861667 | 0.8515 | 103.128 s | 912 MiB | `eb60107e…` | `8d28287b…` |
| mlgym_breakout_minatar | 61.248 s / 22.486719 | 61.781 s / 22.486719 | 22.885938 | 183.744 s | 634 MiB | `cec562e6…` | none (simulated) |
| mlgym_houseprice | 5.059 s / 23344.767385 | 4.876 s / 23344.767385 | 30295.671017 | 15.177 s | CPU 8 cpus | `88d359f2…` | `73ee5597…` |

- Values cross-checked directly from `runs/**/run_record.json` (`outcome.value`, `elapsed_seconds_info_only`,
  `sealed.*`, `limits.provisional_timeout_seconds: 1800.0`, `timeout_factor: 3.0`) and from each result md's
  B1/B2 table (e.g. `U2_ISO_MLAB_IMDB_RESULT_20261119.md:159-169`, `U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_…:238-248`,
  `U2_ISO_MLGYM_HOUSEPRICE_RESULT_…:250-260`). Every 3×B1 equals the census timeout exactly.
- Pins/manifests are the **committed-file** `frozen_pin_sha256` values (C-K5 convention): e.g.
  cifar10 `1f047ad7cc8c…494c2` (`…RESULT:58-60`), imdb `4b1019a6…` (`…:54-55`), ogbn `bd71fdf4…` (`…:55-56`),
  mlgym cifar10 `2d7e533b…` (`…:55-56`), fmnist `eb60107e…` (`…:55-56`), breakout `cec562e6…` (`…:90-92`),
  HousePrice `88d359f2…` (`…:114-116`, `verify_full.summary.txt:3`). Data manifests match the `data_manifest.txt`
  / `prep/manifest.txt` captures (`43fdf860…`, `a87254e1…`, `91312162…`, `c0ef1168…`, `8d28287b…`,
  `73ee5597…`); breakout has no manifest by design (`…RESULT:45`).
- Cards/cpusets match the records: cifar10 UUID `GPU-aa340032…` = card 1, imdb/fmnist `GPU-f439cca8…` = card 2,
  ogbn/breakout `GPU-3b36edea…` = card 6, mlgym cifar10 `GPU-3719bd35…` = card 7 (card indices are the
  `nvidia-smi` index in each result's `gpu/gpu_mid.txt`); HousePrice CPU cpuset `79,78,77,76,59,42,34,28`
  (`limits.cpu_list`, `verify_full.summary.txt:4`). Record paths (`u2_iso_*`) are the seven directories present
  under `docs/r1/reports/trackg_g0_20261117/`.
- Each directory has exactly **9 `run_record.json` = 8 executed + refused `s001` (`scope_violation`,
  `executed:false`)**; `DONE`/`RESULT_STATUS` show `CHECKLIST_E_PASSED` for all seven (the cifar10/breakout/
  HousePrice first `STOP` lines are the preserved v1-verifier false negatives, re-verified as
  `DONE_PASS_CORRECTED`; disclosed at `…CIFAR10_RESULT:258`, `…BREAKOUT_RESULT:288-290` and
  `…HOUSEPRICE_RESULT:399`).
- For every one of the 56 executed records: `isolation.effective: true`, `waivers {}`, `exceptions []`,
  `log_intact: true`, `log_bytes_from_run > 0`, result-channel sha present, `cgroup.kill.empty_after: true`,
  `process.timed_out: false`; and every node's `cgroup_probe.txt` shows inside-scope
  `memory.max=8589934592` / `memory.swap.max=0` (e.g. `u2_iso_mlab_cifar10_…/cgroup_probe.txt`).
- Paper-A gate: all seven `gate/gate_check.txt` show `verdict: clear_finished`,
  `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`, `unidentified_apps: 0`.
- Data outside the repository and no `synthetic` marker (all seven; HousePrice `data_manifest` has
  `synthetic` absent, `…HOUSEPRICE_RESULT:68`; breakout is simulated, no manifest).

### 1.2 Isolation / licence / HousePrice provenance / kitchen / readiness

- **Isolation & co-tenancy.** Confirmed: before/mid/after GPU snapshots for the six GPU nodes, CPU
  before/mid/after for HousePrice; the census's "idle GPU ... (HousePrice: selected CPU cpuset)" and the
  VRAM-upper-bound wording (`:25-27`) match the result records, including HousePrice's narrowed CPU co-tenancy
  evidence (H3) and Breakout's all-8-card `jax.devices()` precheck disclosure.
- **ENGINEERING_ONLY / no evidence / no noise floor / no D21 / no D28 / no T1 label** — matches
  `R1-TRACKG-G0-GO` ("G.0 produces no noise-floor or D21 conclusion") and every result.
- **HousePrice provenance.** Author Kaggle `train.csv` sha256
  `1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41` and md5
  `80ccab65fb115cbad143dbbd2bcd5577` verified from `prep/manifest.txt:16,24`, `prep/setup.log:7`,
  `prep/csv_verify.txt:7-10`, `verify_full.json:3-4`; `--from-file` used and MLGym's copy not used
  (`prep/setup.log`, `prep/manifest.txt` `provided_by`/`from_file_name`; `…HOUSEPRICE_RESULT:322-327`).
- **Kitchen / kit tips / fix.** `mac-trackg-iso-mlab-20261117` @ `fb6e7d73…` and
  `mac-trackg-iso-mlgym-20261117` @ `f07875de…` are the accepted kit-update tips
  (`TRACKG_ISO_KIT_UPDATE_20261119.md:44-45`), both carrying the accepted fix `5403392e`
  (`…:4,20,44-45`); condition 6 PASS / condition 7 blocked on Ada is exactly
  `HARNESS_ISOLATION_FIX_20261119.md:3-4` and its review. Envs (`envs/torch312` Python 3.12.16 /
  torch 2.6.0+cu124 for the five torch nodes + HousePrice; `envs/jax312` after removing
  `nvidia-cuda-nvcc-cu12` for Breakout) match `JAX_ENV_FIX_20261119.md:1-22` and every result.
- **Readiness per `R1-TRACKG-G3-EARLY`** (`PLAN:1330`): the six earlier nodes are the six G3-EARLY names;
  HousePrice "joins now" is supported by the ACCEPTED result review (`b2c463a7…`; corrections H1–H10/S1–S5
  applied — corrected result md sha `0b1212e3…` and `SHA256SUMS` `7607fc5c…` verified) and
  `…HOUSEPRICE_RESULT:6-8`; autoresearch joins only after smoke + U2; the census does not block G.1b/G.4.
  **This is correct and not overclaimed.**
- **Blocked list otherwise correct.** HousePrice and Breakout are passed; no other node is wrongly blocked.
  The autoresearch condition-7 status (blocked) and "U2 not run" under isolation are directionally right
  (see m3/m4 for precision defects).

---

## 2. Findings

### B1 — BLOCKING: the census funnel/appendix is absent, so the mandated mlab_imdb baseline provenance line is missing

`R1-TRACKG-PORT-DECISIONS` (3) (`PLAN:1289`) accepts the imdb baseline only if it is frozen/reviewed **and**
"在 census 漏斗与附录中注明 'baseline 由我们编写'" — noted in the **census funnel and appendix** as "baseline
written by us". The requirement is repeated by the record chain: `mlab_imdb` result
`U2_ISO_MLAB_IMDB_RESULT_20261119.md:50` ("the census **funnel and appendix must note 'baseline written by
us'**"), its unit `unit/U2_ISO_MLAB_IMDB_UNIT_20261119.md:28`, the port report
`docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md:98-99` and the preserved run-level `LICENCES.md:21,30`.

The census has no funnel and no appendix; its only licence sentence (`TRACKG_U4_CENSUS_20261120.md:27-31`)
groups "MLAgentBench tasks/**IMDb**/OGB arXiv generic citation" and never says the mlab_imdb baseline
(DistilBERT fine-tuning) was written by us. As written, a reader of the U4 census would attribute our own
baseline to MLAgentBench. The missing funnel/appendix is also required by `R1-TRACKG-G0-GO:1258`
("census 报告与各 suite 筛选漏斗") and by the U4 definition (`TRACKG_G0_ADA_CENSUS_20261116.md:80-83`:
per-suite funnel, raw records, functional qualification, non-qualifiers to the R1-BX-D12 appendix), and by the
result-level requirement that the census funnel/appendix carry the licence lines for Breakout
("gymnax-derived Apache-2.0 parts are **used** by this node", `…BREAKOUT_RESULT:82-86`) and HousePrice
(Kaggle terms, `--from-file`, not MLGym's copy, `…HOUSEPRICE_RESULT:322-327`). The census's prose covers
Breakout/HousePrice, but it cannot satisfy a requirement on "the census funnel and appendix" while neither
exists, and the imdb note is missing outright. **Fix before acceptance.**

### M1 — MAJOR: the U4 row fields are incomplete; the HousePrice row is also column-shifted

The accepted five-node review states the values the U4 row must carry, including "the **committed-file pin as
the census value** and the **deployed run-record pin separately**", "the **whole-smoke CPU/RAM aggregate**",
"disk free before/after, the gate capture" (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md:134,502-507`). G.0's raw
cost is defined as "run time, peak VRAM, **CPU/RAM**" (`TRACKG_G0_ADA_CENSUS_20261116.md:31-33`). The census
table (`:12-20`), the panel of prose at `:22-27` notwithstanding, does **not** carry:

- the whole-smoke **CPU/RAM aggregate** for any row (the records do have it: `time -v` max RSS
  1,402,612 kB / 1,659,008 kB / 1,256,776 kB / 1,493,864 kB / 1,213,024 kB / 1,262,488 kB / 599,392 kB at
  each result md's `time -v` paragraph, e.g. `…MLAB_CIFAR10_RESULT:161`, `…HOUSEPRICE_RESULT:241`); `:25`
  says only "whole-smoke CPU/RAM aggregates labelled";
- the **deployed run-record pin** separately (only the committed pin column exists; the review's table at
  `TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md:134` gives both);
- the **disk before/after** and the **gate capture/verdict** per row (only "gate clear" prose at `:24`; the
  gate JSON/paths are in each `gate/`);
- for HousePrice, `:20` has **13 cells against the 14-cell header** (`:12-13`): the whole-smoke-bound cell is
  missing, so "CPU 8 cpus" lands in the *whole-smoke upper bound* column and the committed pin, manifest and
  record then shift one column left — the row cannot be parsed mechanically as written, and the 599,392 kB
  RSS bound never appears in the census.

This is a raw-cost/row-content gap in the census deliverable, not a record defect (the records are complete);
fix the rows and the HousePrice row cell count.

### MINOR

- **m1 (metric-key naming).** The five accuracy rows (`:14-18`) show bare B1/B2 numbers; the result docs
  explicitly require the census row to name `val_accuracy` and keep `test_accuracy` separate
  (`…MLAB_CIFAR10_RESULT:171`, `…MLAB_IMDB_RESULT:156-157`, `…OGBN_ARXIV_RESULT:158`,
  `…MLGYM_CIFAR10_RESULT:158`, `…FMNIST_RESULT:158`). Only Breakout (`val_return`) and HousePrice
  (`val_rmse`) are named.
- **m2 (GPU/cpus field).** `GPU/cpus` gives only the local card index for GPU rows (stable UUIDs and the
  cpusets 0-7/8-15 that the records carry are omitted) and "CPU 8 cpus" for HousePrice without its cpuset
  `79,78,77,76,59,42,34,28`; `whole-smoke upper bound` mixes a VRAM bound with a cpuset label and should name
  the unit (VRAM vs RAM).
- **m3 (autoresearch option-A bullet).** `:48` says "code review ACCEPTED" without the review's actual verdict
  detail — **0 BLOCKING, 1 MAJOR (report-only), 6 MINOR, conditions C1–C6** — and without citing the review
  record (`docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md`, sha `261a03e9…`); it cites the code-unit
  report by bare filename, which is **not present in this worktree** (it is at
  `.claude-worktrees/harness_ar_cond7_20261120/docs/r1/reports/trackg_g0_20261117/…`, sha `370782ab…`), and the
  pinned `7330338` is the **docs-only review-fix revision** (the review's object was HEAD `13786d1f`; the
  revision applies M1/C1 and m1–m6 but is itself unreviewed). `:49` "pending an idle GPU" omits the other
  pending step: the branch is **local-only / not pushed** (`TRACKG_AR_COND7A_CODE_UNIT_20261120.md:11`;
  kit-update review C-K5), which is part of the hand-off before the smoke (AR review C2/C6).
- **m4 ("U2 not run" imprecision).** `:45-46` says "U2 not run". The **un-isolated 17 Nov U2 for
  `autoresearch_fixedtokens` PASSED** (`CHECKLIST_E_PASSED`; `TRACKG_U2_AR_RESULT_20261117.md:3`;
  B1 67.901 s), and the census itself cites that B1 at `:50`. Say "isolated U2 not run" and note that the
  17 Nov row predates `R1-HARNESS-ISOLATION`.
- **m5 (condition 6/7 citation).** `:37-38` ("condition 6 PASS; condition 7 ... blocked") cites no source and
  reads contrary to `HARNESS_ISOLATION_HOST_CHECK_20261119.md:6-7,72-78`, which records condition 6 *failing*
  and condition 7 BLOCKED/NOT TESTED **before** the fix. Cite `HARNESS_ISOLATION_FIX_20261119.md:3-4` (sha
  `0ff9a7f2…`) and its review (sha `c8e468c7…`, ACCEPTED, condition 6 PASS / condition 7 blocked) at
  `5403392e`.
- **m6 (pre-launch refusals).** `:7-8,22` "one accepted unit and one smoke per node (no retry)" is true of the
  executed smokes but omits that Breakout attempt 1 was a **pre-launch gate STOP** (`verdict: unknown`,
  no smoke; `…BREAKOUT_RESULT:145-153`) and HousePrice attempt 1 was a **pre-launch CPU-idle STOP**
  (`…HOUSEPRICE_RESULT:173-181,330-334`). Add "one executed smoke each; attempt 1 refused before launch" so
  "no retry" is not read as "no second attempt".
- **m7 (licence/availability per node).** `:27-31` is per-suite prose, not per-node licence/availability
  columns; U1 states it supplies the U4 census's licence/availability columns
  (`U1_LICENCE_AVAILABILITY_20261117.md:264,§8`). Add the per-node provenance lines (including the imdb note,
  B1) and the availability status.
- **m8 (authority and acceptance citations).** The census claims accepted units/results but cites neither the
  per-node unit/result reviews nor the accepted kit-update report/review; its licence claims rest on
  `R1-TRACKG-LICENCES` (not in the authority list, `:3-6`); the U4 basis docs
  (`TRACKG_CENSUS_20261117.md`, the U1 audit) are not referenced. Add the acceptance/citation chain.
- **m9 (record paths).** `:14-20` record paths are relative with no base directory; state
  `docs/r1/reports/trackg_g0_20261117/`.
- *Observation (not a finding):* the readiness paragraph (`:53-56`) could add the G.4-pilot consequence of
  G3-EARLY (`mlgym_breakout_minatar` as the pilot fallback while autoresearch is not ready) and note
  `R1-T1-HOST-H200` as the G.1b/G.4 host row; neither is required by the census and neither is claimed.

---

## 3. Conditions for acceptance (documentation only — no new run, no record/measurement edit)

- **C1 (closes B1).** Add the U4 per-suite funnel and non-qualifier appendix (or an explicit section stating
  where the funnel/appendix lives and why it is not yet part of this report), and carry the mandated
  per-node provenance lines in it, including verbatim for `mlab_imdb`: "The mlab_imdb baseline (DistilBERT
  fine-tuning) was written by us; MLAgentBench ships only a skeleton for this task."; plus the existing
  Breakout (gymnax Apache-2.0 used) and HousePrice (Kaggle terms, `--from-file`, not MLGym's copy) lines.
  If the funnel is deliberately deferred to G.1b, say so explicitly and do not claim the census satisfies
  R1-TRACKG-G0-GO's "census report **and** per-suite funnel" until it does.
- **C2 (closes M1).** Complete the U4 rows: whole-smoke CPU/RAM aggregate (from each `time -v`), the deployed
  run-record pin separately from the committed-file pin, disk before/after and gate capture/verdict per row;
  fix the HousePrice row to 14 cells with the RAM bound value (599,392 kB) in the bound column; label VRAM vs
  RAM.
- **C3 (closes m1/m2).** Name `val_accuracy` as the B1/B2 `outcome.value` metric for the five accuracy rows,
  keep the sealed `test_accuracy` separate, and name the units/IDs in `GPU/cpus`/bound columns (UUID and
  cpuset; VRAM vs RAM).
- **C4 (closes m3).** Correct the autoresearch bullet: state the review's 1 MAJOR (report-only)/6 MINOR and
  conditions C1–C6; cite the review sha `261a03e9…` and the code-unit report sha `370782ab…` with its
  worktree path; distinguish reviewed HEAD `13786d1f` from tip `7330338` (docs-only C1/M1 fix, unreviewed);
  state the branch is local-only/not pushed; say the smoke is gated on C1 acceptance + hand-off + an idle GPU.
- **C5 (closes m4/m5/m6).** Say "isolated U2 not run" (the un-isolated 17 Nov U2 passed, `TRACKG_U2_AR_RESULT_20261117.md:3`);
  cite `HARNESS_ISOLATION_FIX_20261119.md` + `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` for condition 6
  PASS / condition 7 blocked and note the host-check doc is the pre-fix record; disclose the two attempt-1
  pre-launch refusals.
- **C6 (closes m7/m8/m9).** Add the per-node licence/availability columns and the authority/acceptance
  citation chain (`R1-TRACKG-LICENCES`, accepted kit update report/review, per-node unit/result reviews, U4
  basis docs), and state the record base directory.

After C1–C6 the census should be re-reviewed (fresh reviewer; this review is not a re-review and authorises no
run, no record edit, no commit/push, no census launch, no T1/G.1b/G.4 action). Nothing in this review changes
a measured number, a pin, a manifest or an isolation record; the seven rows remain supported by the accepted
records.

---

## 4. Attestation

Read-only review. The only file written is this review (uncommitted); no smoke/U2/GPU/Ada/SSH/HTCondor/
deepthought action; no unit, result, capture, record, pin or manifest was edited; no commit/push/delete. Commands
used (all read-only, 20 November 2026, Europe/Berlin): `sha256sum` of the census, result mds, `SHA256SUMS`,
reviews and reports named above; `wc`, `ls`, `sed -n`, `grep`, `git show/rev-parse/log/branch/status`,
`git merge-base --is-ancestor`; Python `json` reads of all **63** `run_record.json` files (56 executed + 7
refused `s001`) and of the pins/manifest/verifier summaries; greps of each directory's `cgroup_probe.txt`,
`data_manifest.txt`, `prep/manifest.txt`, `pins.txt`, `gate/gate_check.txt`, `RESULT_STATUS.txt`/`DONE`,
`SHA256SUMS`, `invocation_inner.sh` and result md; Python comparison of each census row's values against the
run records and result mds; checks that the result-md entry inside each `SHA256SUMS` equals the actual file
hash and that each `SHA256SUMS` sha equals the value in the corresponding corrections record.
No live-host state is claimed beyond what these preserved records contain.
