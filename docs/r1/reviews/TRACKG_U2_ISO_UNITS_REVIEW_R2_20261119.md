# Independent re-review R2 — Track G G.0 U2 isolated-node units, five nodes (19 November 2026)

**Reviewer.** Fresh independent re-reviewer (`u2-iso-unit-reviewer-r2`), delegated by the coordinator after the
round-1 review; no involvement in drafting the units or the round-1 fixes. Read-only: no code or unit edit, no
commit/push, no GPU/U2/census run, no deletion, no HTCondor/deepthought, no Ada login. The only file written is
this review record (uncommitted). Worktree files were read in place; the authority documents that exist only on
published `main` (the port-isolation report, its review, and the `R1-TRACKG-PORT-DECISIONS` /
`R1-HARNESS-ISOLATION` PLAN rows) were read with `git show origin/main:…` (no checkout, no write).

**Objects under review.** Five one-node U2 raw-cost units, revision 2, in `docs/r1/proposals/u2_iso_20261119/`
(all untracked; 67 lines each; canonical bytes):

| Unit | sha256 |
|---|---|
| `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` | `cf7e4e681897c7246d9622dddf9c709a20c175b29e0713dc266f3bc77bb1b75f` |
| `U2_ISO_MLAB_IMDB_UNIT_20261119.md` | `c52456b40b9eb909ba953fb375112432ae172ba9fc27bf753a0ca14eeed52c66` |
| `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` | `8b0c32a58933573e92a6f0c726e386ef2ba33d6a08747478ff854c3e99b04eb4` |
| `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` | `ab05e7b3b9a5d812feb05f42dfe870c794b2b7d1fe2317614ce75ab1657da88b` |
| `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` | `76bcf490616bac0ade54328ea992ebc36e9c910f4e7ba8dc24b8243e4ef5eedd` |

**Verdict summary: all five units NOT ACCEPTED again — 0 BLOCKING, 3 shared MAJOR (M1, M2, M5) and 8–9 MINOR
each.** M3 (validated command) is now fixed; M4 (GPU floor/co-tenancy) and M6 (scope/STOP set) are largely fixed
(launch floor, three-point census, explicit STOP set) with the residual MINORs below. The revision fixed the
round-1 minors m1, m2, m8, m9 and most of m3–m7, but it introduced one new census-critical regression: **the
committed-file and deployed pins are inverted in all five units** (M5), so the census row would commit the
deployed per-record pin while believing it is the committed-file pin — exactly what the accepted kit report
§3/§10.2 and review C-K5 warn against. M1 and M2 remain partially fixed: the peak-VRAM label is self-contradictory
and absent from the record list, and the cgroup construction is given in the wrong order with no enforcement
check.

---

## 1. Authority, evidence and worktree state

**Worktree.** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`, HEAD
`1cc54d81` (`ops-tasl-20261116`), untracked unit directory `?? docs/r1/proposals/u2_iso_20261119/`; the round-1
review is the only other untracked file. HEAD diverged from published `main`: merge-base `45fb94cc`;
`origin/main` = **`de3de54fd22dcdd86215be0924307e36a64ed08b`** = authority `de3de54f` (`git rev-parse origin/main`).
`R1-TRACKG-PORT-DECISIONS` (`origin/main:docs/r1/PLAN.md:1289`), `R1-HARNESS-ISOLATION` (`:1290`) and the
port-isolation report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` live only at `origin/main`;
they were read with `git show origin/main:…`. (The worktree `docs/r1/PLAN.md` carries rows `R1-TRACKG-G0-GO:1258`
and `R1-TRACKG-LICENCES:1269` but not the two rows above.) The kit-update report/review and their captures are
worktree files.

**Authority read.**
- `R1-TRACKG-G0-GO` — `PLAN.md:1258`: one node per unit, each independently reviewed, ENGINEERING_ONLY census,
  re-check idle card/sharing/Paper A gate each time, no noise floor/D21/D28.
- `R1-HARNESS-ISOLATION` — `PLAN.md:1290`: separate process for editable code, append-only metric log, cgroup-wide
  kill, no T1 label/RL before the isolation unit.
- `R1-TRACKG-PORT-DECISIONS` — `PLAN.md:1289`: rule (4) node timeout = 3 × census-measured baseline; a timeout is
  the proposal's failure, not an infrastructure rerun; census on Python 3.12; rules (1)–(3) MLGym licence,
  HousePrice, imdb baseline disclosure.
- Port report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2 (how every node runs), §3(3)
  imdb disclosure sentence, §7 steps 2–4; its review `origin/main:docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md`
  (round 4 ACCEPTED).
- Accepted kit update `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  **`fe232e2b…`** (reviewed bytes were `3c3ae74a…`; see §10), and its review
  `worktree:docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`, sha256 `d8c68f9f…`, **ACCEPTED**, 0
  BLOCKING / 0 MAJOR, 5 MINOR, conditions C-K1…C-K5.
- Isolation-fix review `worktree:docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256 `c8e468c7…`,
  **ACCEPTED**; C2 = this kit update (commit the recomputed `frozen_pin_sha256` values in the census), C3 = no
  autoresearch GPU run until the logits-transfer decision + `cuda_open` init fix are reviewed.
- Prior accepted U2 result `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_U2_AR_RESULT_20261117.md` and its
  R2 review `worktree:docs/r1/reviews/TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md` (§9 is the result-row standard the
  template still departs from).
- Kit-update captures `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119_captures/`
  (`pins/`, `smoke/attempt2/<node>/{s000_baseline,s001,…}/run_record.json`, `smoke/attempt2/*.log`,
  `scripts/smoke_one.sh`; the accepted review verified all 341 capture hashes).

**Method and limits.** This is a paper review plus capture cross-check; no GPU/U2 run and no Ada login. Every
node-specific value was re-derived from the accepted kit report §2–§7 and the captured smoke records (baseline
run time/outcome, `AR_DATA manifest_sha256`, deployed `frozen_pin_sha256`, `limits.external_limit`, smoke
header `worktree tip:`). Where a finding depends on live-kit semantics I cite the same documents the units cite
as authority. No live-host state is claimed beyond what the accepted kit-update/fix reviews already verified.

---

## 2. Round-1 findings re-check (direct answer to the six questions)

| Round-1 finding | Status in revision 2 | Where |
|---|---|---|
| **M1 peak VRAM** | **PARTIAL — still MAJOR.** A 1 s `nvidia-smi --query-compute-apps=pid,used_memory --format=csv -l 1` sampler and the "no per-run peak" rule are now required, and the "whole-smoke upper bound" fallback is present. But the label is self-contradictory: a whole-smoke maximum cannot be "attributed to the baseline process tree", and the query omits `gpu_uuid`, so co-tenants on other cards cannot be separated; no PID-tree→run attribution method is given. The sampler maximum, command, interval and output path are **not in the required result-file field list**. | `:45-49`, `:53-56` |
| **M2 cgroup construction** | **PARTIAL — still MAJOR.** The outer `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` wrap and `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` are now mandatory, and the `--memory-limit` record string matches the captured `smoke_one.sh`/record exactly. But the unit gives the `CG`/export as a step *before* the wrap; the validated `smoke_one.sh` computes it **inside** the `systemd-run … bash -c` (captures `scripts/smoke_one.sh`). Executed literally the export points at the caller's cgroup, not the delegated scope, so the 8 GiB cap would not bind the smoke. The round-1 required enforcement probe (small cap + overshoot) and `memory.max`/`memory.swap.max` read inside the scope are still absent; the run records carry `limits.external_limit`/`memory_method: external` but no cap read. | `:34-36`, `:37-42` |
| **M3 validated command** | **RESOLVED.** The unit now specifies `PYTHONPATH=src`, `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…`, `CUDA_VISIBLE_DEVICES=""`, `AR_TRACKG_DATA_ROOT=…`, `taskset -c <cpus>` and `which python` + resolved-invocation recording. This matches the kit update §7 attempt-2 invocation and `smoke_one.sh` in substance. | `:37-42` |
| **M4 GPU floor/co-tenancy** | **RESOLVED as defined** (residual MINOR): ≥ 8 GiB free and no other user's compute app; `nvidia-smi` free/used/utilization + compute-app census before/mid/after; STOP if no qualifying card or an unrecorded card switch. Still missing: the basis for 8 GiB (the prior accepted run-1 floor was ≥ 24 GiB), and any rule for a card that fills or gains a co-tenant mid-run (invalidate/record), not only at launch. | `:43-45` |
| **M5 census pin/kit identity** | **NOT FIXED — now MAJOR, and worse than round 1.** Both pin values are present and the tip/tracked-clean launch check, gate capture and census-row instruction are there, but the **labels are inverted in all five units**: the hash labelled "committed-file pin" is the deployed per-record pin and vice versa (see §4 M5). The census row would therefore commit the deployed pin. | `:15-17`, `:55` |
| **M6 scope/STOP completeness** | **RESOLVED as defined** (residual MINORs): explicit no T1 label, no HTCondor/deepthought, no deletion, no cross-node pooling, no evidence/no noise/D21/D28; STOPs for gate, wrong/dirty kit, data/env, other users, non-effective/waivers, synthetic, timeout/OOM, any executed record non-effective, disk < 50 GiB (cap 100 GiB) and cross-node/evidence/T1; no timeout/OOM retry; preserve captures. Still missing: "no push" (it says "no force push"), an explicit autoresearch (C3-blocked)/HousePrice (STOP)/Breakout (not run) exclusion, "no other host", the disk filesystem(s), and a no-resume/whole-rerun statement. | `:7-8`, `:58-61` |
| m1 report citation (not a PLAN row) | **RESOLVED** — cites `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7 and explicitly says "(not a PLAN row named R1-TRACKG-PORT-ISOLATION)". Minor residual: the accepted kit-update report/review bytes are not cited by path/sha, and imdb/ogbn licence lines do not cite `R1-TRACKG-LICENCES`. | `:4-8`, `:26` |
| m2 3 × B1 timeout recorded | **RESOLVED** — provisional 1800 s; no timeout/OOM retry; node timeout 3 × measured B1 recorded. | `:6-7`, `:50-52` |
| m3 setup/static tests | **PARTIAL** — the kit bullet says setup/static-test results are recorded (setup command, manifest shas, CPU-masked static tests), but the required result-file field list does not include them (no command/log path/sha, file count/size, read-only bit, `du`/`df`, interpreter). | `:24-25` vs `:53-57` |
| m4 gate capture | **PARTIAL** — "captured immediately before launch" and "gate capture" are required, but not the JSON path/sha/UTC, newest `live_*` = configured run dir, or the self-excluded `pgrep` result. | `:18-20`, `:56` |
| m5 result-file/row | **PARTIAL** — a result-file field list exists, but no result-file name/path and no per-run `run_record.json`/`run.log` paths+sha256, `killed_with`, `determinism.not_forced`, one JSON line per run, `CHECKLIST_E_PASSED` or the 8 executed + refused frozen-diff (9 records) structure. | `:50-57` |
| m6 MLGym licence | **PARTIAL** — `mlgym_cifar10` cites `R1-TRACKG-LICENCES` and CC BY-NC 4.0/Apache-2.0 scope; `mlgym_fmnist` cites the CC BY-NC scope but not the row and not the Apache-2.0 sentence. | `:26` |
| m7 imdb baseline provenance | **PARTIAL/INACCURATE** — says "the baseline was written by us in the accepted U3 kit (disclosed), no upstream baseline copy". Port decision (3) requires the sentence "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships only a skeleton for this task", and records that neither the census funnel nor the appendix carries it yet — so "(disclosed)" is wrong, and the required sentence/skeleton clause is missing. | `:26` |
| m8 no-deletion/preserve | **RESOLVED** — "preserve, do not delete" and "no deletion". | `:8`, `:57` |
| m9 s001 refused vs executed | **RESOLVED** — "every **executed** run record … effective:true" and the refused `s001` record is explicitly `executed:false` and not a failure; the STOP is also qualified "any executed record". | `:27-30`, `:60` |

**Verdict on the six questions:** M3 fixed; M4 and M6 fixed as defined with MINOR residues; **M1 and M2 remain
incomplete MAJORs**; **M5 is now wrong in a census-critical way** (inverted pins).

---

## 3. What I verified as correct (node-specific)

All five units are the same 67-line template with node-specific substitutions. Every substituted value is
correct against the accepted kit update and its captures:

| Unit | Suite / node | Kit branch @ tip (verified against kit report §2 and captured smoke header `worktree tip:`) | Data `data_manifest.json` sha256 (verified against captured baseline `run.log` `AR_DATA manifest_sha256=…`) | Pre-run reference quoted (verified against `<node>/s000_baseline/run_record.json`) |
|---|---|---|---|---|
| mlab_cifar10 | MLAgentBench / `mlab_cifar10` | `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` | `43fdf860…` (log: files=4) | `12.859 s / val 0.5152` (record: 12.859, outcome 0.5152) |
| mlab_imdb | MLAgentBench / `mlab_imdb` | same @ `fb6e7d73…` | `a87254e1…` (log: files=11) | `61.399 s / val 0.9048` (record: 61.399, 0.9048) |
| mlab_ogbn_arxiv | MLAgentBench / `mlab_ogbn_arxiv` | same @ `fb6e7d73…` | `91312162…` (log: files=6) | `5.702 s / val 0.275982` (record: 5.702, 0.275982) |
| mlgym_cifar10 | MLGym / `mlgym_cifar10` | `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf` | `c0ef1168…` (log: files=4) | `24.07 s / acc 0.491` (record: 24.07, 0.491) |
| mlgym_fmnist | MLGym / `mlgym_fmnist` | same @ `f07875de…` | `8d28287b…` (log: files=4) | `26.702 s / acc 0.861667` (record: 26.702, 0.861667) |

Also correct in every unit: one node only; ENGINEERING_ONLY census with no evidence/no noise floor/D21/D28; the
unit does not claim a T1 label run; Ada host only; `envs/torch312` (Python 3.12.16, torch 2.6.0+cu124 — the
correct env for both MLGym nodes; only Breakout uses `envs/jax312`, kit report §9); data root outside the
repository; no synthetic marker allowed; `isolation.effective:true`/`waivers {}`/`exceptions []` requirement and
STOP on non-effective/synthetic; `port_smoke_gpu` node, `--gpu-uuid`, `--cpus`, `--runs-root` outside the repo,
`--provisional-timeout 1800`; the kit update's pre-run references are explicitly labelled **reference only**;
no unit claims a U3/unisolated run; none includes autoresearch, HousePrice or Breakout; the kit-update tips and
data manifests are post-update and current.

**Expected pin values (accepted kit report §3 table vs §3 deployed note / §7 table):**

| node | committed-file pin (census convention) | deployed run pin (in `run_record.json`) |
|---|---|---|
| mlab_cifar10 | `1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2` | `a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388` |
| mlab_imdb | `4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb` | `c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0` |
| mlab_ogbn_arxiv | `bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7` | `5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad` |
| mlgym_cifar10 | `2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e` | `817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62` |
| mlgym_fmnist | `eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3` | `ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee` |

**Note on the delegation's node-specific list.** The task's parenthetical lists the pairs as
`mlab_cifar10 a459b3d8/1f047ad7`, `mlab_imdb c169a6b8/4b1019a6`, `mlab_ogbn 5ff5824a/bd71fdf4`,
`mlgym_cifar10 817c9034/2d7e533b`, `mlgym_fmnist ef804338/eb60107e`. Read as "committed/deployed" that order
contradicts the accepted sources; the sources are unambiguous: the *committed-file* pins are the kit report §3
table (`1f047ad7 / 4b1019a6 / bd71fdf4 / 2d7e533b / eb60107e`, reproduced in captures `pins/new_*.json`) and
the *deployed* pins are the run-record `frozen_pin_sha256` values (`a459b3d8 / c169a6b8 / 5ff5824a / 817c9034 /
ef804338`, reproduced in `pins/deployed_*.json`). I resolve the mapping against the accepted report, not the
task's ordering; revision 2 follows the task ordering, which is the M5 error below.

---

## 4. Findings shared by all five units

Severity follows the delegation rule: any BLOCKING/MAJOR means the unit is NOT ACCEPTED. Line numbers are the
template's; the per-unit sections repeat them against each unit's own path.

### BLOCKING

None. The units are correctly scoped to one node and do not authorise an excluded/blocked node, a T1 label run,
or another host; the kit identities and data manifests are right.

### MAJOR

**M1 — Peak VRAM: the sampler is new, but the label is self-contradictory and the number is not in the record
(`:43-49`, `:53-56`).** The unit now says the torch-node log carries no per-run VRAM field and requires a 1 s
`nvidia-smi --query-compute-apps=pid,used_memory --format=csv -l 1` sampler for the whole smoke, reported "as a
labelled whole-smoke upper bound **attributed to the baseline process tree**", with a fallback "if attribution
is impossible, record it as a whole-smoke upper bound and say so". Three defects remain:
1. **The two labels are mutually exclusive.** A whole-smoke maximum includes the s002/s003/E1…E4/B2 runs and any
   co-tenant on the card; it is not the baseline process tree's footprint. If it is attributed to the baseline
   tree (by PID/cgroup filtering), it is a baseline-window measurement, not a whole-smoke upper bound. The unit
   must choose one and define it.
2. **The query cannot support attribution or card separation.** `--query-compute-apps=pid,used_memory` omits
   `gpu_uuid`, so with 8 cards (kit report §6: six busy cards at launch) used-memory from other cards/co-tenants
   is indistinguishable; no rule maps host PIDs to the run's process tree/cgroup (the worker runs in a PID
   namespace).
3. **It is not a required record field.** The result-file list has "GPU free/used/utilization + app census at
   three points" but not the sampler command/interval/output path/maximum or its label; the census row's VRAM
   number can therefore be omitted or recorded unlabelled. The prior accepted standard required exactly this
   (`TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md` §9 item 6/9: "measured baseline peak (method/attribution) or the
   labelled whole-smoke upper bound, sampler command/interval/attribution").
**Required:** choose and define one measurement — (a) baseline-window sampler (open at baseline run start,
`gpu_uuid,pid,used_memory`, PID→cgroup/process-tree filter, record command/interval/file/max) or (b) a
whole-smoke maximum explicitly labelled "upper bound, includes co-tenants and non-baseline runs", with the
sampler fields added to the required result-file list; never call a whole-smoke maximum a baseline attribution.

**M2 — Cgroup construction is present but ordered wrong and unverified (`:34-36`, `:37-42`).** The outer
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` wrap, `Delegate=yes`, `MemorySwapMax=0`
and `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` are now required, and the `--memory-limit` record string
(`external: … (enforced cgroup)`) exactly matches the captured `smoke_one.sh` and the run records'
`limits.external_limit`. Two defects:
1. **Ordering.** The unit lists `CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`
   *before* "wrap the whole smoke in `systemd-run …`". The validated `smoke_one.sh` computes and exports both
   **inside** the `systemd-run --user --scope … -- bash -c '…'`; executed literally, the unit's order points
   `AR_TEST_CGROUP_PARENT` at the caller's cgroup, so the per-run cgroups and the 8 GiB cap are not under the
   delegated scope (`limits.cgroup_parent` would not be the scope path captured in every accepted record). The
   unit must state "inside the wrapped scope".
2. **No enforcement evidence.** Round-1 required the one-off enforcement probe (a small cap + an overshoot) and
   the `memory.max`/`memory.swap.max` values read **inside** the scope, recorded, with STOP if not enforceable.
   Revision 2 keeps only "cgroup/memory cap" in the field list; the accepted run records prove the scope shape
   but carry no cap read, so a run claiming an 8 GiB cap is still asserting it. The prior accepted standard
   required the probe and the `memory.max`/`memory.swap.max` read (§9 item 8).
**Required:** move the `CG`/`AR_TEST_CGROUP_PARENT` export inside the wrapped shell; add the cap probe and the
in-scope `memory.max`/`memory.swap.max` read (STOP if not enforceable) to the procedure and the record list.

**M5 — Census pin convention is inverted in all five units (census-critical regression).** Every unit
(`:15-17`) labels the **deployed** run pin as "committed-file pin" and the **committed-file** pin as "deployed
run pin", then tells the census to use the "committed-file pin (kit report §3/§10.2)". The accepted sources are
unambiguous:
- kit report §3 table header "new pin (committed node files)": mlab_cifar10 `1f047ad7…`, mlab_imdb `4b1019a6…`,
  mlab_ogbn `bd71fdf4…`, mlgym_cifar10 `2d7e533b…`, mlgym_fmnist `eb60107e…` (`:85-90`);
- kit report §3 deployed note (`:96-103`) and §7 table (`:236-242`): the run records' `frozen_pin_sha256` are
  the **deployed** pins `a459b3d8… / c169a6b8… / 5ff5824a… / 817c9034… / ef804338…`; §10.2 (`:300-305`) repeats
  "the fix report's table is the committed-file pin (no data link), the smoke records are deployed pins";
- captures: `pins/new_mlab.json:22` pin `1f047ad7…` vs `pins/deployed_mlab.json:23` pin `a459b3d8…`;
- captured baseline records: `smoke/attempt2/<node>/s000_baseline/run_record.json` `frozen_pin_sha256` =
  `a459b3d8… / c169a6b8… / 5ff5824a… / 817c9034… / ef804338…`;
- kit-update review C-K5 (`:284-287`): "The census must commit the pins with the stated convention
  (committed-file pin, §3 table)".

The units' instruction is not merely a label swap: the "deployed run pin" they name is a hash that appears in
**no** run record, so "record the deployed pin with the run" cannot be satisfied as written, and the census row
would commit `a459b3d8…` (deployed) as the committed-file identity. **Required:** swap the two values in every
unit to the table above, cite kit report §3/§10.2 and review C-K5 for the convention, and record both as full
64-hex values (see m-n1).

### MINOR

- **m1 — report cited, but kit-update report/review bytes and licence rows not cited (`:4-8`, `:26`).** Fixed for
  the non-existent `R1-TRACKG-PORT-ISOLATION` row; the accepted kit-update report (`TRACKG_ISO_KIT_UPDATE_20261119.md`)
  and its review are cited only as "accepted kit update", without path/sha; imdb/ogbn licence lines do not cite
  `R1-TRACKG-LICENCES` (`PLAN.md:1269`).
- **m3 — setup/static tests asserted but not in the required record list (`:24-25` vs `:53-57`).** The kit bullet
  says they are recorded but the result-file list omits the setup command/log, manifest shas, CPU-masked static
  test command/result, file count/size, read-only bit and `du`/`df` (prior standard §9 item 7).
- **m4 — gate capture lacks the round-1 detail (`:18-20`, `:56`).** No JSON path/sha256/UTC, newest `live_*` =
  configured run dir, or self-excluded `pgrep` result (census §4; prior standard §9 item 5).
- **m5/n4 — result-file/row incompleteness and a lost pass criterion (`:50-57`).** No result-file name/path; no
  per-run `run_record.json`/`run.log` paths+sha256, `killed_with`, `determinism.not_forced`, one JSON line per
  run; no `CHECKLIST_E_PASSED` token and no "8 executed runs + refused frozen diff (9 records)" expectation (the
  round-1 review §2 recorded these as present and correct in revision 1 — they are absent now, a regression).
- **m-n1 — pins abbreviated (`:16-17`).** Four of five units give the committed/deployed pins only as prefixes
  (`c169a6b8…`, `1f047ad7…`, …); the census row needs the full 64-hex values (table in §3).
- **m-e — GPU floor basis / mid-run rule (`:43-45`).** ≥ 8 GiB free is stated without basis (the prior accepted
  run-1 floor was ≥ 24 GiB; the kit's ~2.85 GB is a point-in-time snapshot of a sibling chain, not a measured
  peak); no rule if free VRAM falls below baseline peak + 2 GiB, or a co-tenant app appears, in the baseline
  window; "no unrecorded card switch" would permit a recorded switch.
- **m-n2 — metric field names not stated (`:53-55`).** The result must name the census metric (`val_accuracy` for
  MLAgentBench nodes, `accuracy`/`test_accuracy` for MLGym nodes; kit report §7 table).
- **m-n3 — scope/STOP residue (`:7-8`, `:58-61`).** "no force push" (not "no push"); no explicit
  autoresearch (C3-blocked)/HousePrice (STOP)/Breakout (not run) exclusion; no "no other host/TASL-7/TASL-2"
  beyond HTCondor/deepthought; "no T1 label" but not "no T1 sweep"; disk threshold without the filesystem(s) or
  footprint accounting; no resumability statement (a STOP is not resumed; an interrupted unit re-runs whole
  from a new `<runs-root>`).
- **m6 (MLGym units) — `mlgym_fmnist` licence row/sentence (`:26`).** Cites the CC BY-NC 4.0 scope but not
  `R1-TRACKG-LICENCES` and not the Apache-2.0 scope sentence that `mlgym_cifar10` carries; correct it to match.
- **m7 (imdb) — disclosure (`:26`).** As in §2.

---

## 5. Unit verdict — `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_cifar10`; kit `mac-trackg-iso-mlab-20261117` @ `fb6e7d73…`
(correct post-update tip; not the pre-tip `0aae2f6`); data manifest `43fdf860…` (confirmed in the captured
baseline log, files=4); pre-run `12.859 s / val 0.5152` (confirmed in `s000_baseline/run_record.json`);
`envs/torch312` correct; no U3 claim. Pin values are correct but their two labels are swapped: the unit calls
`a459b3d8…` (the deployed run-record pin) the "committed-file pin" and `1f047ad7…` (the §3 table committed pin)
the "deployed run pin" (`:16-17`). Note that this unit is the only one that gives the swapped "committed" value
in full and the "deployed" value truncated, so the census-size identity is still incomplete.

**Findings (file:line).**
- MAJOR M1 `:43-49`, `:53-56`; M2 `:34-36`, `:37-42`; M5 `:15-17`, `:55`.
- MINOR m1 `:4-8`, `:26`; m3 `:24-25`; m4 `:18-20`, `:56`; m5/n4 `:50-57`; m-n1 `:16-17`; m-e `:43-45`;
  m-n2 `:53-55`; m-n3 `:7-8`, `:58-61`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 3 MAJOR, 8 MINOR).

**Conditions.** Fix M1 (define one VRAM measurement and add it to the record list), M2 (compute
`CG`/`AR_TEST_CGROUP_PARENT` inside the scope; add the cap probe and in-scope `memory.max`/`memory.swap.max`),
and M5 (swap the pins; committed-file `1f047ad7…`, deployed `a459b3d8…`, both full 64-hex; cite kit report
§3/§10.2 and review C-K5). Apply the MINORs (at minimum m3/m4/m5-n4, m-n1, m-e, m-n3). Then resubmit for a
fresh independent review; do not execute this node before acceptance.

## 6. Unit verdict — `U2_ISO_MLAB_IMDB_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_imdb`; same kit/tip `fb6e7d73…`; data manifest `a87254e1…`
(confirmed, files=11); pre-run `61.399 s / val 0.9048` (confirmed); `envs/torch312` correct; no U3 claim. Pins
swapped: the unit calls `c169a6b8…` (deployed) the "committed-file pin" and `4b1019a6…` (committed) the
"deployed run pin" (`:16-17`), both truncated. Provenance/disclosure issue at `:26`: "(disclosed)" is inaccurate
and the port-decision (3) sentence is not carried (m7).

**Findings.**
- MAJOR M1 `:43-49`, `:53-56`; M2 `:34-36`, `:37-42`; M5 `:15-17`, `:55`.
- MINOR m1 `:4-8`, `:26`; m3 `:24-25`; m4 `:18-20`, `:56`; m5/n4 `:50-57`; m-n1 `:16-17`; m-e `:43-45`;
  m-n2 `:53-55`; m-n3 `:7-8`, `:58-61`; m7 `:26`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 3 MAJOR, 9 MINOR).

**Conditions.** As §5; for M5 use committed-file `4b1019a6…` / deployed `c169a6b8…`; carry the exact port
decision (3) sentence into the unit and the result/funnel duty. Fresh review after revision; no execution before
acceptance.

## 7. Unit verdict — `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_ogbn_arxiv`; same kit/tip `fb6e7d73…`; data manifest `91312162…`
(confirmed, files=6); pre-run `5.702 s / val 0.275982` (confirmed); `envs/torch312` correct; no U3 claim; the
port report's residual risk that this worker holds the full labels on disk is a kit-level disclosure already
accepted by the port review and is not charged here. Pins swapped: `5ff5824a…` (deployed) labelled committed and
`bd71fdf4…` (committed) labelled deployed (`:16-17`), both truncated.

**Findings.**
- MAJOR M1 `:43-49`, `:53-56`; M2 `:34-36`, `:37-42`; M5 `:15-17`, `:55`.
- MINOR m1 `:4-8`, `:26`; m3 `:24-25`; m4 `:18-20`, `:56`; m5/n4 `:50-57`; m-n1 `:16-17`; m-e `:43-45`;
  m-n2 `:53-55`; m-n3 `:7-8`, `:58-61`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 3 MAJOR, 8 MINOR).

**Conditions.** As §5; for M5 use committed-file `bd71fdf4…` / deployed `5ff5824a…`. Fresh review after
revision; no execution before acceptance.

## 8. Unit verdict — `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_cifar10`; kit `mac-trackg-iso-mlgym-20261117` @ `f07875de…` (correct
post-update tip; not `061d638`); data manifest `c0ef1168…` (confirmed, files=4); pre-run `24.07 s / acc 0.491`
(confirmed); `envs/torch312` is the correct environment for this node (only Breakout uses `envs/jax312`, kit
report §9) — the "wrong package/env for MLGym" suspicion does not apply. Licence line (`:26`) is adequate
(`R1-TRACKG-LICENCES` + CC BY-NC 4.0/Apache-2.0 scope). Pins swapped: `817c9034…` (deployed) labelled committed
and `2d7e533b…` (committed) labelled deployed (`:16-17`), both truncated.

**Findings.**
- MAJOR M1 `:43-49`, `:53-56`; M2 `:34-36`, `:37-42`; M5 `:15-17`, `:55`.
- MINOR m1 `:4-8`; m3 `:24-25`; m4 `:18-20`, `:56`; m5/n4 `:50-57`; m-n1 `:16-17`; m-e `:43-45`;
  m-n2 `:53-55`; m-n3 `:7-8`, `:58-61`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 3 MAJOR, 8 MINOR).

**Conditions.** As §5; for M5 use committed-file `2d7e533b…` / deployed `817c9034…`. Fresh review after
revision; no execution before acceptance.

## 9. Unit verdict — `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_fmnist`; kit `mac-trackg-iso-mlgym-20261117` @ `f07875de…`; data
manifest `8d28287b…` (confirmed, files=4); pre-run `26.702 s / acc 0.861667` (confirmed); `envs/torch312` is
correct (same reasoning as §8; not jax); no U3 claim. Pins swapped: `ef804338…` (deployed) labelled committed
and `eb60107e…` (committed) labelled deployed (`:16-17`), both truncated. Licence line (`:26`) omits
`R1-TRACKG-LICENCES` and the Apache-2.0 scope sentence that `mlgym_cifar10` carries (m6).

**Findings.**
- MAJOR M1 `:43-49`, `:53-56`; M2 `:34-36`, `:37-42`; M5 `:15-17`, `:55`.
- MINOR m1 `:4-8`; m3 `:24-25`; m4 `:18-20`, `:56`; m5/n4 `:50-57`; m-n1 `:16-17`; m-e `:43-45`;
  m-n2 `:53-55`; m-n3 `:7-8`, `:58-61`; m6 `:26`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 3 MAJOR, 9 MINOR).

**Conditions.** As §5; for M5 use committed-file `eb60107e…` / deployed `ef804338…`; add the `R1-TRACKG-LICENCES`
row and Apache-2.0 scope wording. Fresh review after revision; no execution before acceptance.

---

## 10. Cross-unit, independence and the round-1 process note

**Independence/scope.** Each unit names exactly one node/suite with its own kit branch/tip, data manifest, run
root and pre-run reference; none claims another node's result and none authorises an excluded/blocked node or a
T1 label run. The three MLAB nodes share one kit and the two MLGym nodes share the other, as
`R1-TRACKG-G0-GO` expects; nothing is pooled. Because they are one template, M1/M2/M5 are replicated in all
five, and each unit must be revised and re-reviewed separately — acceptance of one is not acceptance of the
others and none may be executed on the strength of this review.

**Kit-update report sha change (round-1 process note).** The worktree kit-update report is sha256
**`fe232e2b…`** (`350` lines); the accepted review records the reviewed bytes `3c3ae74a…` and conditions
C-K1…C-K4 to apply M-1…M-4 before the report is committed/cited. I verified the current text carries every
correction: M-1 six untracked data links (`TRACKG_ISO_KIT_UPDATE_20261119.md:323-324`); M-2 correct 01:52:57Z
pre-run GPU snapshot and 02:08Z gate clarification (`:167`); M-3 evidence-index capture-vs-live paths,
`smoke/chain_{A,B}_attempt2.log`, and `summary_<node>`/`records_<node>` distinction (`:341`); M-4 the
C2-mandated BLOCKED-state-check wording with C3 explicitly still in force (`:274-277`); M-5 "~2.85 GB
(2,853 MiB)" and "each node's own card returned to 5 MiB/0 %" (`:175-177`). The sha change is therefore
**consistent** with the accepted C-K1…C-K4 record fixes, and no unit relies on the reviewed bytes: the units do
not cite the report sha, and every value they take from the report (tips, data manifests, pre-run references,
pin convention wording) is identical in the current text. The accepted kit-update review's C-K5 remains the
controlling text for the census pin convention.

**One residual process discrepancy (not a per-unit finding).** The kit-update report still says the kit branches
are "not pushed" (`:4`, `:47-50`, `:299-301`, §10.1), while HEAD commit `1cc54d81`'s subject says "kit branches
pushed". The units are unaffected (they check local `git rev-parse HEAD` == tip and `--untracked-files=no`
clean, which holds whether or not the branches were pushed), but the operator should not cite the report's
push status as current, and the report should be corrected or annotated before the census record cites it.
`R1-TRACKG-PORT-DECISIONS`, `R1-HARNESS-ISOLATION` and the port report exist only on `origin/main` (published
`de3de54f`), not in this worktree's tree; the unit citations resolve against published `main`, and the branch
carrying these units must not be cited/committed as if the cited rows were in its own tree until it is merged
with `main`.

---

## 11. Summary and required fixes

| Unit | MAJOR | MINOR | Verdict | Required before any execution |
|---|---|---|---|---|
| `mlab_cifar10` | 3 (M1, M2, M5) | 8 | **NOT ACCEPTED** | Define/label/record one VRAM measurement; put `CG`/`AR_TEST_CGROUP_PARENT` inside the scope + cap probe/`memory.max`; swap pins (committed `1f047ad7…` / deployed `a459b3d8…`); minors |
| `mlab_imdb` | 3 (M1, M2, M5) | 9 | **NOT ACCEPTED** | Same, committed `4b1019a6…` / deployed `c169a6b8…`; carry the port-decision (3) imdb sentence correctly |
| `mlab_ogbn_arxiv` | 3 (M1, M2, M5) | 8 | **NOT ACCEPTED** | Same, committed `bd71fdf4…` / deployed `5ff5824a…` |
| `mlgym_cifar10` | 3 (M1, M2, M5) | 8 | **NOT ACCEPTED** | Same, committed `2d7e533b…` / deployed `817c9034…` |
| `mlgym_fmnist` | 3 (M1, M2, M5) | 9 | **NOT ACCEPTED** | Same, committed `eb60107e…` / deployed `ef804338…`; add `R1-TRACKG-LICENCES`/Apache-2.0 scope |

**Required fix set per unit (plus node-specific minors).**
1. **M1:** one defined VRAM measurement — baseline-window sampler with `gpu_uuid,pid,used_memory` and a
   PID/cgroup attribution rule, or an explicitly "upper bound, includes co-tenants and non-baseline runs"
   whole-smoke maximum; record sampler command/interval/output path/maximum in the result file; never call a
   whole-smoke maximum a baseline attribution.
2. **M2:** compute/export `CG` and `AR_TEST_CGROUP_PARENT` **inside** the `systemd-run --user --scope -p
   Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` wrap; add the enforcement probe and the in-scope
   `memory.max`/`memory.swap.max` read, recorded; STOP if not enforceable.
3. **M5:** correct the pin convention and values (committed-file = kit report §3 table; deployed = run-record
   `frozen_pin_sha256`), record both full 64-hex, census row uses the committed-file pin (kit report §3/§10.2;
   review C-K5).
4. Apply the MINORs: setup/static-test fields, gate-capture detail, the §9 result-row fields
   (`CHECKLIST_E_PASSED`, 8 executed + refused diff, per-run record paths/sha256, `killed_with`,
   `determinism.not_forced`, one JSON line per run), full pins, floor basis and mid-run contamination rule,
   metric names, the scope/STOP wording additions, and the node-specific imdb/fmnist issues.
5. Resubmit each unit for a fresh independent review; **no unit may be executed on the strength of this
   review.**

**Attestation.** This review is uncommitted and is the only file written. I did not run the smoke or any
GPU/U2/census job, did not edit the units or any code, did not commit/push/delete anything, and did not touch
HTCondor, deepthought, TASL-7/TASL-2 or Ada. All citations were read from this worktree or `git show origin/main`
/ the committed captures; no live-host state is claimed beyond what the accepted kit-update/fix reviews already
verified.

### Reviewer's read-only command record (19 Nov 2026, Europe/Berlin)

- `git rev-parse origin/main` (`de3de54f`), `git merge-base HEAD origin/main` (`45fb94cc`), `git log`,
  `git status --short` (only the untracked unit directory and the round-1 review), `sha256sum` of the five
  units and the authority files (`fe232e2b…`, `d8c68f9f…`, `c8e468c7…`).
- `git show origin/main:docs/r1/PLAN.md` (rows `R1-TRACKG-G0-GO:1258`, `R1-TRACKG-LICENCES:1269`,
  `R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`); `git show
  origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` (§2/§3/§7 read); `git show
  origin/main:docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md` (head/round-4 ACCEPTED); `git show
  origin/main:docs/r1/reports/TRACKG_U3_PORT_MLAB_20261117.md` (imdb baseline provenance).
- Read the accepted kit-update report and review, the isolation-fix review, the prior U2 AR result and its R2
  review (§9), the census report §4, and the kit-update captures: `pins/new_*.json` vs `deployed_*.json`,
  five `s000_baseline/run_record.json` + `run.log` (`elapsed_seconds_info_only`, outcome, manifest sha,
  `frozen_pin_sha256`, `limits.external_limit`, `isolation` fields), the `s001` record, and
  `scripts/smoke_one.sh` (cgroup/`AR_TEST_CGROUP_PARENT`/`PYTHONPATH=src`/`PATH`/`taskset`/`--memory-limit`
  string).
- Grep checks: `peak_vram` present only in the autoresearch run logs (torch-node logs have no VRAM line); the
  `frozen_pin_sha256` in every captured torch baseline record equals the deployed pin
  (`a459b3d8/c169a6b8/5ff5824a/817c9034/ef804338`), not the §3 committed-file pin
  (`1f047ad7/4b1019a6/bd71fdf4/2d7e533b/eb60107e`); the captured `worktree tip:` headers equal the tips the
  units quote.
