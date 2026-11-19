# Independent review — Track G G.0 U2 raw-cost units on the isolated kits, five nodes (19 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-iso-unit-reviewer`), delegated by the coordinator; no prior involvement in
these five units, the kit update, the isolation fix, or the census. Read-only: no code or unit edit, no commit/push, no
GPU/U2/census run, no deletion, no HTCondor/deepthought, no Ada login. The only file written is this review record
(uncommitted). All unit/authority files were read from the Mac worktree; the two authority documents that exist only on
published `main` were read read-only from `origin/main` via `git show` (no checkout, no write).

**Objects under review.** Five one-node U2 raw-cost units in `docs/r1/proposals/u2_iso_20261119/` (all untracked,
44 lines each, canonical bytes):

| Unit | sha256 |
|---|---|
| `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` | `85508014e3f1b97c6baf732198524154cb5e104b7ff9e0fd0ccc7cb4655e01ab` |
| `U2_ISO_MLAB_IMDB_UNIT_20261119.md` | `795af8e0b931763115c1d14d1bca7e3177b6f723fdca5b3594b2afbe83f1fae2` |
| `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` | `6ddafb542430a7cd4f933e8ad3ed5ca1cb6bacda66cb77655c20e125f9ce80c1` |
| `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` | `4f40e0cda772e0aca7e6d036677ac507a1ab35607b6ed38ba033393bd7f67479` |
| `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` | `a53e231b524ba3ca8362c1be2682a8ca3bd71adff4a6aee5d8121b4cb3e4d871` |

**Verdict summary: all five units NOT ACCEPTED — 0 BLOCKING, 6 MAJOR and 7–8 MINOR each (30 MAJOR, 38 MINOR total).** The node-specific
substitutions (kit branch/tip, suite, node, data manifest sha256, pre-run reference, metric name) are all correct; the
defects are shared template omissions that are execution-critical or census-critical (peak-VRAM source, cgroup
enforcement, literal invocation, GPU footprint/co-tenancy, kit-pin record/identity check, scope/STOP completeness).
Per-unit verdicts and conditions are in §5–§9; the summary is in §11.

---

## 1. Authority, evidence and worktree state

**Worktree.** `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`, HEAD
`1cc54d81` (`ops-tasl-20261116`), untracked unit directory `?? docs/r1/proposals/u2_iso_20261119/`. HEAD diverged from
published `main`: merge-base `45fb94cc`; `origin/main` = **`de3de54fd22dcdd86215be0924307e36a64ed08b`** = authority
`de3de54f` (`git rev-parse origin/main`). `R1-TRACKG-PORT-DECISIONS` and the port-isolation report live only at
`origin/main` (the older reviews record the same gap); they were read with `git show origin/main:…` and every citation
below resolves there unless marked as a worktree file.

**Authority read.**
- `R1-TRACKG-G0-GO` — `origin/main:docs/r1/PLAN.md:1258`: one node per unit, each independently reviewed, ENGINEERING_ONLY
  census, re-check idle card/sharing/Paper A gate each time, no noise floor/D21/D28.
- `R1-HARNESS-ISOLATION` — `origin/main:docs/r1/PLAN.md:1290`: separate process for editable code, append-only metric
  log, cgroup-wide kill, no T1 label/RL before the isolation unit.
- `R1-TRACKG-PORT-DECISIONS` — `origin/main:docs/r1/PLAN.md:1289`; rule (4): node timeout = 3 × census-measured
  baseline; a timeout is the proposal's failure, not an infrastructure rerun; census on Python 3.12.
- Port report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2 (how every node runs) and §7 (steps
  for the experiment agent); review `origin/main:docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md`
  (ACCEPTED, round 4).
- Accepted kit update `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`
  (sha256 `fe232e2b…`; note the review cites the reviewed bytes `3c3ae74a…` — see §10) and its review
  `worktree:docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256 `d8c68f9f…`, **ACCEPTED**, 0 BLOCKING /
  0 MAJOR, 5 MINOR, conditions C-K1…C-K5).
- Isolation fix review `worktree:docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha256 `c8e468c7…`,
  **ACCEPTED**, condition 6 PASS, condition 7 BLOCKED/documented; C2 = the kit update, C3 = no autoresearch GPU run
  until the logits-transfer design change + `cuda_open` init fix are reviewed).
- Prior accepted U2 pattern `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_U2_AR_RESULT_20261117.md` and
  `worktree:docs/r1/reviews/TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md` (sha256 `f827637b…`, ACCEPTED; its M1–M12 and §9
  result-record list are the standard this template departs from).
- Kit-update captures `worktree:docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119_captures/`
  (`SHA256SUMS` verified by the accepted kit-update review: 341/341; all baselines, logs, summaries, GPU snapshots and
  `scripts/smoke_one.sh` read for this review).

The authority text the units need exists; the units' problems are not missing authority but incomplete execution/record
text and one mis-cited authority label (§4 m1).

---

## 2. What I verified as correct (node-specific)

All five units are the same 44-line template with only node-specific substitutions. I checked every substituted value
against the accepted kit update and its captures; every one is correct:

| Unit | Suite / node | Kit branch @ tip (verified against kit update §2 and the captured smoke header `worktree tip:`) | Data `data_manifest.json` sha256 (verified against the captured baseline `run.log` `AR_DATA manifest_sha256=…`) | Pre-run reference quoted (verified against `<node>/s000_baseline/run_record.json`) |
|---|---|---|---|---|
| mlab_cifar10 | MLAgentBench / `mlab_cifar10` | `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` | `43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3` | `12.859 s / val 0.5152` |
| mlab_imdb | MLAgentBench / `mlab_imdb` | same @ `fb6e7d73…` | `a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c` | `61.399 s / val 0.9048` |
| mlab_ogbn_arxiv | MLAgentBench / `mlab_ogbn_arxiv` | same @ `fb6e7d73…` | `9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c` | `5.702 s / val 0.275982` |
| mlgym_cifar10 | MLGym / `mlgym_cifar10` | `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf` | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` | `24.07 s / acc 0.491` |
| mlgym_fmnist | MLGym / `mlgym_fmnist` | same @ `f07875de…` | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` | `26.702 s / acc 0.861667` |

Also correct in every unit: one node only; ENGINEERING_ONLY census, no evidence/noise floor/D21/D28 stated; the unit
does not claim a T1 label run (the explicit must-not statement is missing — M6); Ada host only; `envs/torch312` (3.12.16, torch 2.6.0+cu124) with the kit-update smokes; data root outside
the repository; no synthetic marker allowed; `isolation.effective:true` / `waivers {}` / `exceptions []` requirement
and STOP on non-effective/synthetic; `port_smoke_gpu` node, `--gpu-uuid`, `--cpus`, `--runs-root` outside the repo,
`--provisional-timeout 1800`; `CHECKLIST_E_PASSED`; "8 executed runs + refused frozen diff" (9 records) — this matches
the captured PASS nodes; the pre-run references are explicitly labelled **reference only**; no unit claims a U3 or
unisolated run; none includes autoresearch, HousePrice or Breakout.

Deployed pins (from the captured baseline records, cross-checked with kit update §7) are also consistent:
mlab_cifar10 `a459b3d8…`, mlab_imdb `c169a6b8…`, mlab_ogbn_arxiv `5ff5824a…`, mlgym_cifar10 `817c9034…`,
mlgym_fmnist `ef804338…`; committed-file pins are kit update §3's `1f047ad7… / 4b1019a6… / bd71fdf4… / 2d7e533b… /
eb60107e…`.

---

## 3. Method and limits

This review is a **paper review plus capture cross-check**, not a live-host review: the task forbids a GPU/U2 run and I
did not log in to Ada. The kit-branch tips, pins and copies were accepted on live Ada by the kit-update review
(0 BLOCKING/0 MAJOR; tips/pins reproduced independently there); I re-checked their values against the accepted report
and the captured smoke headers/records. Where a finding depends on the kit's actual invocation semantics
(`port_smoke_gpu` flags, cgroup/`AR_TEST_CGROUP_PARENT`, `CHECKLIST_E` record shape) I cite the accepted kit-update
report, its `scripts/smoke_one.sh` capture, and the port report §7 — the same documents the units cite as authority.

---

## 4. Findings shared by all five units

Severity follows the delegation rule: any BLOCKING/MAJOR means that unit is NOT ACCEPTED. Line numbers below are the
template's; the per-unit sections repeat them against each unit's own path.

### BLOCKING

None. The units are correctly scoped to one node and do not authorise an excluded/blocked node, a T1 label run, or
another host; the kit identities and data manifests are right.

### MAJOR

**M1 — Peak VRAM has no source: "from the baseline log" is false for all five nodes (unit:32).** The unit's record list
requires `peak_vram_mb` "from the baseline log". The five nodes are torch nodes; their baseline `run.log` contains no
`peak_vram_mb` (or any `vram`) line, and `run_record.json` has no VRAM key. Only the (excluded) autoresearch worker
prints it: captures
`…/smoke/attempt2/autoresearch_fixedtokens/s000_baseline/run.log:528` `AR_INFO peak_vram_mb=1980.1`; a grep for `vram`
over the five torch node run logs/records returns nothing. The kit update's "~2.85 GB (2,853 MiB)" is a point-in-time
`nvidia-smi` snapshot of the **sibling chain's** card, not a per-run measurement: the kit-update review's M-5 records
`mlgym_cifar10/gpu_after.txt` = GPU 2 at 2,853 MiB/60 % while that node's own GPU 6 is 5 MiB/0 % (captures confirm).
The census's raw-cost peak VRAM therefore cannot be produced as specified. Required: specify a measurement — e.g. a 1 s
`nvidia-smi --query-compute-apps=pid,used_memory` sampler attributed to the baseline run's process tree (window opened at
the baseline run start, not the run-dir mtime), or an explicitly labelled whole-smoke maximum "upper bound, includes
co-tenants" — and record the sampler command/interval/attribution. Never call an unattributed snapshot the baseline
footprint.

**M2 — The 8 GiB cgroup is asserted, not constructed; the recorded string is not enforcement (unit:14, unit:26).** The
unit says "8 GiB delegated cgroup (`MemoryMax=8G`)" and passes
`--memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"`. In the
accepted kit update that string is only the `limits.external_limit` record; the enforcement is the **outer** wrapper in
`…/captures/scripts/smoke_one.sh`:
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '… export
AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup) …'`. Port report §7 step 3 says "Set
`AR_TEST_CGROUP_PARENT` to the delegated cgroup", and the same section states the smoke itself does **not** check
isolation (the record checker does). A literal reading of the unit gives no outer scope and no `AR_TEST_CGROUP_PARENT`;
`port_support.limits()` then waives `no_cgroup`, the record's `waivers` is non-empty and `effective` false, which the
unit's own STOP (unit:36-37) turns into a failed run. Required: give the exact outer `systemd-run … Delegate=yes`
command, export `AR_TEST_CGROUP_PARENT`, add the one-off enforcement probe (small cap + overshoot) and record
`memory.max`/`memory.swap.max` read inside the scope; STOP if not enforceable.

**M3 — The command is not the validated invocation and is not self-contained (unit:24-27).** The accepted kit-update
attempt-2 invocation is `PATH=…/envs/torch312/bin:$PATH PYTHONPATH=src CUDA_VISIBLE_DEVICES=
AR_TRACKG_DATA_ROOT=… taskset -c 0-7 <env python> -m tests.trackg.port_smoke_gpu …` (kit update §7; the same shape is in
`smoke_one.sh`). The units give the `python -m …` line only with "from the kit worktree, cpuset set, env first on PATH,
`CUDA_VISIBLE_DEVICES=""`" and omit `PYTHONPATH=src`, the explicit `PATH`/`VIRTUAL_ENV` activation and `which
python python3` record, the `taskset` position inside the cgroup scope, and `AR_TRACKG_DATA_ROOT` from the command
(it is only in the env bullet at unit:16). The accepted invocation sets `PYTHONPATH=src`; the unit omits it, so the
command is not the validated one (and `src/` is not on the interpreter's default path, so the `autoresearch` package
is not importable from the kit root). Required: replace it with the literal invocation and recording requirements
above.

**M4 — Pre-run GPU footprint is undefined and co-tenancy evidence is absent (unit:13-14, unit:32, unit:36).** The STOP
is "no idle GPU/free < footprint", but no footprint/floor is defined; "one idle GPU only" does not say how idle is
judged or recorded. The record list has only "GPU before/after" — no free/used at launch, no co-tenant
apps/pids/`used_memory`, no `utilization.gpu`, no mid-smoke sample in the baseline window, no rule for a card that fills
mid-run and no "no unrecorded card switch". This is exactly the round-2 MAJOR-3/M5 pattern the prior accepted U2 unit
fixed with a declared ≥24 GiB run-1 floor ("no measured footprint exists yet; later units use measured peak + 2 GiB")
and launch/mid/end co-tenant sampling. The kit update's host had six other cards busy at launch (four at 100 %
utilisation), so this is not hypothetical. Required: state the floor and its basis, sample
`nvidia-smi --query-gpu=uuid,index,memory.free,memory.used,utilization.gpu` and
`--query-compute-apps=gpu_uuid,pid,used_memory` at launch, mid-baseline and end; STOP/record if free VRAM falls below
baseline peak + 2 GiB or the sample is contaminated; no unrecorded card switch.

**M5 — Census pin record and kit-identity verification are missing (unit:11-12, unit:31-35).** Port report §7 step 4:
"The census commits each node's `frozen_pin_sha256` and measured baseline run time." Kit update §3 ("Deployed-pin note,
important for the census") and §10.2: records carry a **deployed** pin that also hashes the data symlink (e.g.
mlab_cifar10 `a459b3d8…` vs committed-file `1f047ad7…`); "the census must commit one documented convention — … and not
compare the two by accident". Fix review C2 and kit-update review C-K5 repeat the same. The units' record list mentions
none of: `frozen_pin_sha256`, the committed-vs-deployed convention, the kit worktree HEAD-equals-tip / tracked-clean
check at launch (the accepted kit update leaves only the expected untracked `data` links), or the Paper A gate capture
path/sha/UTC. A run from a wrong/dirty kit would then yield a census row under a claimed identity that nothing in the
unit verifies or records in the required form. Required: add the pin fields/convention, the launch-time tip/tracked-clean
check with STOP, and the gate capture record.

**M6 — Scope/STOP completeness is below the accepted standard (unit:7, unit:36-38).** The unit says ENGINEERING_ONLY
census, but has no explicit "no T1 label/sweep", no "no HTCondor/deepthought/other host", no "no deletion/push", no
"nothing counted as evidence", and no statement that autoresearch (C3-blocked), HousePrice (STOP) and Breakout (not run)
are out of scope / no cross-node authorisation is claimed. Its STOP list is the six-line short form: it lacks a STOP for
a wrong/dirty kit, data-setup/manifest re-verification failure (only "data manifest mismatch" after the fact),
env/freeze mismatch, static/smoke environment failure, or another user's process/files being touched; "disk below floor"
(unit:38) has no value or filesystem (the accepted pattern used a 100 GB unit/total cap and a <50 GB STOP). The
inclusion of the five nodes is substantively correct, but the authorising document does not carry the must-not/STOP set
the plan and the prior accepted unit require. Required: add the explicit must-not list and the missing STOPs with
numeric thresholds.

### MINOR

**m1 — `R1-TRACKG-PORT-ISOLATION` is not a PLAN row (unit:7).** `git show origin/main:docs/r1/PLAN.md | grep -c
"R1-TRACKG-PORT-ISOLATION"` = 0 (rows are `R1-TRACKG-PORT-DECISIONS` at :1289 and `R1-HARNESS-ISOLATION` at :1290).
Cite the accepted report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7 (and its review) instead; also cite
the kit-update report/review bytes and, for MLGym, `R1-TRACKG-LICENCES`.

**m2 — Timeout: provisional only, 3 × B1 not required in the record (unit:6, unit:33).** Authority rule (4) makes the
node timeout 3 × the measured baseline; the unit records "provisional 1800 s; no timeout permitted" but not the derived
3 × B1 value that the census row needs (prior M7). Add: record B1, 3 × B1 as a derived result, and the provisional
value/semantics.

**m3 — Data setup and static checks are asserted, not executed/recorded (unit:15-17).** Port report §7 step 2 requires the
per-node `setup_command` with `AR_TRACKG_DATA_ROOT` outside the repo and the manifest sha recorded; kit update §5 has the
setup state. The units give only the expected manifest sha and data root, with no setup/re-verify command, setup log,
file count/size, read-only bit or `du`/`df`; no CPU-masked static-test command/result (prior M1/M3/M8). Add them as
record steps (the data setup is idempotent; re-running the setup command re-verifies and re-links).

**m4 — Paper A gate capture not required (unit:13, unit:31-35).** "Clear immediately before launch" is required, but the
record list does not require the gate JSON path/sha/UTC, the newest `live_*` = configured run dir, or the self-excluded
`pgrep` result (prior M9 and `TRACKG_CENSUS_20261117.md` §4). Add.

**m5 — No unit result-file / row requirement (unit:35).** The unit says captures go under
`docs/r1/reports/trackg_g0_20261117/u2_iso_<node>_<UTC>/` but does not require a written per-node result record (the prior
accepted unit required `TRACKG_U2_AR_RESULT_…` or the per-node row file with the §9 field list, including per-run
record paths/sha256, `killed_with`, `determinism.not_forced`, one JSON line per run). Add the result-file name and the
row-field list so U4 can compile rows without re-deriving them.

**m6 — MLGym units: licence provenance not cited (MLGym units unit:4-7).** The MLGym nodes are in
`third_party/mlgym/` with the CC BY-NC 4.0 licence/scope statements (`R1-TRACKG-LICENCES`; port report §3(1)). The
authority line cites none of it. Add `R1-TRACKG-LICENCES` and the licence scope so the census funnel carries it.

**m7 — mlab_imdb: mandated baseline disclosure not carried (imdb unit:4-17).** Port decision (3) requires the census
funnel and paper appendix to say: "The mlab_imdb baseline (DistilBERT fine-tuning) was written by us; MLAgentBench ships
only a skeleton for this task." The imdb unit does not mention it. Add it to the unit/record (it is a disclosure duty,
not a run change).

**m8 — No preserve/no-deletion rule (unit:35).** The prior accepted unit required raw records preserved under
`<runs-root>` and "never delete; an interrupted unit re-runs whole from a new `<runs-root>` (old moved aside)". Add.

**m9 — STOP contradicts the refused `s001` record (unit:37 vs unit:18-19).** The STOP says "any run record not
`effective:true`", but the deliberately refused frozen-diff `s001` record is `executed:false` with
`isolation.effective:null / waivers:null / exceptions:null` by design (kit update §7; every captured `s001` record
confirms). Qualify the STOP as "every **executed** record" (the unit already uses that wording at unit:18).

---

## 5. Unit verdict — `U2_ISO_MLAB_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_cifar10`; kit `mac-trackg-iso-mlab-20261117` @ `fb6e7d73…` (correct
post-update tip, not the pre-tip `0aae2f6`); committed pin `1f047ad7…`; deployed pin `a459b3d8…`; data manifest
`43fdf860…` (confirmed in the captured baseline log); pre-run `12.859 s / val 0.5152` (confirmed: s000
`elapsed_seconds_info_only=12.859`, outcome `val 0.5152`); `envs/torch312` correct; no U3 claim. No node-specific
value is wrong — but the unit inherits every shared finding.

**Findings (unit path lines).**
- MAJOR M1 `:32`; M2 `:14,:26`; M3 `:24-27`; M4 `:13-14,:32,:36`; M5 `:11-12,:31-35`; M6 `:7,:36-38`.
- MINOR m1 `:7`; m2 `:6,:33`; m3 `:15-17`; m4 `:13,:31-35`; m5 `:35`; m8 `:35`; m9 `:37` (m6/m7 not applicable).

**Verdict: NOT ACCEPTED** (0 BLOCKING, 6 MAJOR, 7 MINOR).

**Conditions.** Apply M1–M6 and m1–m5/m8–m9; then resubmit for a fresh independent review (M1–M6 change the
measurement/procedure/record, not just wording). Do not execute this node before that acceptance.

## 6. Unit verdict — `U2_ISO_MLAB_IMDB_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_imdb`; same kit/tip `fb6e7d73…`; committed pin `4b1019a6…`; deployed pin
`c169a6b8…`; data manifest `a87254e1…` (confirmed in the captured baseline log); pre-run `61.399 s / val 0.9048`
(confirmed: s000 `61.399`, outcome `val 0.9048`); `envs/torch312` (transformers stack) correct; no U3 claim. The unit
also omits the mandated "imdb baseline written by us" disclosure (m7).

**Findings.** MAJOR M1 `:32`; M2 `:14,:26`; M3 `:24-27`; M4 `:13-14,:32,:36`; M5 `:11-12,:31-35`; M6 `:7,:36-38`.
MINOR m1 `:7`; m2 `:6,:33`; m3 `:15-17`; m4 `:13,:31-35`; m5 `:35`; m7 `:4-17`; m8 `:35`; m9 `:37`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 6 MAJOR, 8 MINOR).

**Conditions.** As §5 plus m7 (carry the port-decision (3) baseline disclosure into the unit/result/funnel). Fresh
review after revision; no execution before acceptance.

## 7. Unit verdict — `U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md`

**Node-specific check.** MLAgentBench / `mlab_ogbn_arxiv`; same kit/tip `fb6e7d73…`; committed pin `bd71fdf4…`;
deployed pin `5ff5824a…`; data manifest `91312162…` (confirmed in the captured baseline log); pre-run
`5.702 s / val 0.275982` (confirmed: s000 `5.702`, outcome `val 0.275982`); `envs/torch312` correct; no U3 claim. Note
the port report's residual risk that this worker has the full labels on disk is a kit-level disclosure already accepted
by the port review; it does not change this unit's raw-cost procedure and is not charged here.

**Findings.** MAJOR M1 `:32`; M2 `:14,:26`; M3 `:24-27`; M4 `:13-14,:32,:36`; M5 `:11-12,:31-35`; M6 `:7,:36-38`.
MINOR m1 `:7`; m2 `:6,:33`; m3 `:15-17`; m4 `:13,:31-35`; m5 `:35`; m8 `:35`; m9 `:37`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 6 MAJOR, 7 MINOR).

**Conditions.** As §5; fresh review after revision; no execution before acceptance.

## 8. Unit verdict — `U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_cifar10`; kit `mac-trackg-iso-mlgym-20261117` @ `f07875de…` (correct
post-update tip, not `061d638`); committed pin `2d7e533b…`; deployed pin `817c9034…`; data manifest `c0ef1168…`
(confirmed in the captured baseline log); pre-run `24.07 s / acc 0.491` (confirmed: s000 `24.07`, outcome `acc 0.491`);
`envs/torch312` is the correct environment for this node (only Breakout uses `envs/jax312`; the kit-update smoke ran
this node in the torch chain) — the task's "wrong package/env for MLGym" suspicion does not apply to this unit; no U3
claim. Licence provenance is missing from the authority line (m6).

**Findings.** MAJOR M1 `:32`; M2 `:14,:26`; M3 `:24-27`; M4 `:13-14,:32,:36`; M5 `:11-12,:31-35`; M6 `:7,:36-38`.
MINOR m1 `:7`; m2 `:6,:33`; m3 `:15-17`; m4 `:13,:31-35`; m5 `:35`; m6 `:4-7`; m8 `:35`; m9 `:37`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 6 MAJOR, 8 MINOR).

**Conditions.** As §5 plus m6 (cite `R1-TRACKG-LICENCES` and the `third_party/mlgym` CC BY-NC 4.0/Apache-2.0 scope);
fresh review after revision; no execution before acceptance.

## 9. Unit verdict — `U2_ISO_MLGYM_FMNIST_UNIT_20261119.md`

**Node-specific check.** MLGym / `mlgym_fmnist`; kit `mac-trackg-iso-mlgym-20261117` @ `f07875de…`; committed pin
`eb60107e…`; deployed pin `ef804338…`; data manifest `8d28287b…` (confirmed in the captured baseline log); pre-run
`26.702 s / acc 0.861667` (confirmed: s000 `26.702`, outcome `acc 0.861667`); `envs/torch312` correct (same reasoning as
§8); no U3 claim; licence provenance missing from the authority line (m6).

**Findings.** MAJOR M1 `:32`; M2 `:14,:26`; M3 `:24-27`; M4 `:13-14,:32,:36`; M5 `:11-12,:31-35`; M6 `:7,:36-38`.
MINOR m1 `:7`; m2 `:6,:33`; m3 `:15-17`; m4 `:13,:31-35`; m5 `:35`; m6 `:4-7`; m8 `:35`; m9 `:37`.

**Verdict: NOT ACCEPTED** (0 BLOCKING, 6 MAJOR, 8 MINOR).

**Conditions.** As §8; fresh review after revision; no execution before acceptance.

---

## 10. Cross-unit / independence assessment

The five units **are appropriately independent and node-specific in the sense that matters**: each names exactly one
node/suite with its own kit branch/tip, data manifest and pre-run reference; each has its own run root and capture
directory; none claims another node's result and none authorises an excluded/blocked node. The shared host and shared
kit branches (three mlab nodes on one kit, two mlgym nodes on the other) are expected and compatible with
`R1-TRACKG-G0-GO`; they do not share results or evidence. Because they are one template, however, the six MAJOR
omissions are replicated in all five, and each unit must be revised and re-reviewed separately — acceptance of one
must not be read as acceptance of the others.

One process point outside the units: the kit-update report in the worktree is now sha256 `fe232e2b…`, while the
accepted review records the reviewed bytes `3c3ae74a…` and a condition to re-hash after the record fixes (C-K1/C-K2);
and the report says the kit branches are "not pushed" while the HEAD commit message says they were pushed. Neither
changes the correct tips/pins, but before any launch the operator should confirm that the accepted C-K1…C-K4 record
fixes are in the report and that the branch being used is the reviewed tip (`fb6e7d7 / f07875d`) on Ada, whether local
or pushed. This is a note for the root, not a separate per-unit MAJOR.

---

## 11. Summary and required fixes

| Unit | MAJOR | MINOR | Verdict | Required before any execution |
|---|---|---|---|---|
| `mlab_cifar10` | 6 (M1–M6) | 7 | **NOT ACCEPTED** | Peak-VRAM method; cgroup wrap+`AR_TEST_CGROUP_PARENT`+probe; literal validated command; GPU floor/co-tenancy sampling; pin convention + worktree/gate records; scope/STOPs; minors |
| `mlab_imdb` | 6 (M1–M6) | 8 | **NOT ACCEPTED** | Same, plus the port-decision (3) imdb baseline disclosure |
| `mlab_ogbn_arxiv` | 6 (M1–M6) | 7 | **NOT ACCEPTED** | Same (no node-specific extra) |
| `mlgym_cifar10` | 6 (M1–M6) | 8 | **NOT ACCEPTED** | Same, plus `R1-TRACKG-LICENCES`/CC BY-NC scope |
| `mlgym_fmnist` | 6 (M1–M6) | 8 | **NOT ACCEPTED** | Same, plus `R1-TRACKG-LICENCES`/CC BY-NC scope |

**Required fix set (per unit, in addition to the minors):** (i) a real baseline peak-VRAM measurement (1 s
`nvidia-smi --query-compute-apps` sampler attributed to the baseline process tree, or a labelled whole-smoke upper
bound; sampler/interval/attribution recorded); (ii) the exact outer
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` wrap, `AR_TEST_CGROUP_PARENT`, an
enforcement probe and `memory.max`/`memory.swap.max` inside the scope; (iii) the literal validated invocation
(`PATH`, `PYTHONPATH=src`, `AR_TRACKG_DATA_ROOT`, `CUDA_VISIBLE_DEVICES=""`, `taskset` inside the scope) and the
`which python/python3`, `PATH`, `VIRTUAL_ENV` record; (iv) a defined GPU free-VRAM floor (≥24 GiB run-1; measured peak +
2 GiB later), launch/mid/end co-tenant and utilisation samples, and card-fill STOP/no unrecorded switch; (v) the
`frozen_pin_sha256` record with the committed-file-vs-deployed convention, the launch-time kit tip/tracked-clean check
(STOP on mismatch), the Paper A gate capture, and a per-node result file with the prior accepted row fields; (vi) the
explicit must-not/scope set (no T1 label/sweep; autoresearch C3-blocked, HousePrice STOP, Breakout not run, no
cross-node authorisation; no other host/HTCondor/deepthought; no deletion/push; nothing evidence) and the missing STOPs
with numeric disk thresholds; plus the node-specific minors above.

Because M1–M6 change the measurement, the isolation construction, the command and the record, a text-only patch is not
enough: each revised unit needs a fresh independent review before execution. NO unit may be executed on the strength
of this review.

**Attestation.** This review is uncommitted and is the only file written. I did not run the smoke or any GPU/U2/census
job, did not edit the units or any code, did not commit/push/delete anything, and did not touch HTCondor, deepthought,
TASL-7/TASL-2 or Ada. All citations above were read from this worktree or `git show origin/main` / the committed
captures; no live-host state is claimed beyond what the accepted kit-update/fix reviews already verified.

### Reviewer's read-only command record (19 Nov 2026, Europe/Berlin)

- `git rev-parse origin/main` (`de3de54f`), `git merge-base HEAD origin/main` (`45fb94cc`), `git worktree list`,
  `git status --short` (only the untracked unit directory); `sha256sum` of the five units and the authority files;
  `git show origin/main:docs/r1/PLAN.md` (rows G0-GO:1258, PORT-DECISIONS:1289, HARNESS-ISOLATION:1290);
  `git show origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` (whole file, §2/§7 quoted);
  `git show origin/main:docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md` (head/verdict).
- Read the accepted kit-update report and review, the isolation-fix review, the prior U2 AR result and its R2 review,
  the census report, and the kit-update captures: five `s000_baseline/run_record.json` + `run.log` (elapsed/metric/
  manifest/pin/isolation/limits), all `s001` records (`executed:false`, null isolation), `summary_all_torch.json`,
  `gpu_before/gpu_after.txt`, and `scripts/smoke_one.sh` (cgroup/`AR_TEST_CGROUP_PARENT`/`PYTHONPATH=src`).
- Grep checks: `peak_vram_mb`/`vram` present only in the autoresearch logs; no `R1-TRACKG-PORT-ISOLATION` row at
  `origin/main`; no `peak_vram` key in the torch run records.
