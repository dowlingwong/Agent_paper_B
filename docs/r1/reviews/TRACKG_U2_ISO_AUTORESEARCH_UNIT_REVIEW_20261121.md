# Independent review — Track G G.0 U2 unit `autoresearch_fixedtokens` (isolated kit, option A) — 21 November 2026

**Reviewer.** Fresh independent reviewer (`u2-ar-unit-reviewer`), delegated by the coordinator; no involvement in
writing this unit, the option-A code/kit change, its code review, the isolation fix or any earlier U2/AR review.
Read-only: the only file written is this review record (uncommitted). No unit/code edit, no commit/push/delete, no
run/GPU/U2/census job, no Ada login, no TASL/HTCondor/deepthought action. All verification below was done on the Mac
worktrees in place; the harness branch tip and all cited hashes were verified in this session. I did not claim any
live Ada host state beyond what the accepted records and captures show.

**Object under review.** `docs/r1/proposals/u2_iso_20261119/U2_ISO_AUTORESEARCH_UNIT_20261121.md`, sha256
**`3bb015a1ece7c65ac04181f73e4ae84aa12a2d99187dfa82043817ee8c1513ec`**, **56 lines**, **4,489 bytes**, untracked
at review time (worktree `ops-tasl-20261116`, HEAD `5bc4e5c0`). Status in the unit: "proposed unit; run only after a
fresh independent review accepts it and the pre-U2 isolated smoke passes".

**Verdict summary: ACCEPTED — 0 BLOCKING, 2 MAJOR, 14 MINOR, conditional on C1–C8.** The unit's substance is correct
and independently checked: one node only, ENGINEERING_ONLY; the accepted kit branch and tip
(`mac-trackg-iso-ar-cond7a-20261120` @ `7330338`); both pin roles (committed-file `147f0d35…`, 20 entries; deployed
run-record pin `069e987a…`, 21 entries with the `data` link — both reproduced from the kit's own loader/function in
this session); the data manifest `ab7186d2…` (13 files, 963 M); `envs/torch312` (Python 3.12.16, torch 2.6.0+cu124,
freeze `d2e70fe4…`); the option-A no-CUDA-IPC result path (AST scan NONE for `cuda_share`/`cuda_open`/`_share_cuda_`/
`_new_shared_cuda`/`bind_cuda`); the isolation expectation `effective:true`, `waivers {}`, `exceptions []`, private
`/dev/shm` (`shared_dev_shm:false`); the inside-scope cgroup construction with the 8 GiB/0 probe and one-line
`--memory-limit`; the exclusive-idle GPU with a ≥40 GiB floor; the 8-executed + refused-`s001` `CHECKLIST_E_PASSED`
expectation; the B1/B2, 3 × B1 and provisional-1800 s timeout; and the measured-slowdown requirement against the
17 Nov B1 `67.901 s` / `564 s` smoke and the corrected `97–161 s`/`2.4–3.4×` estimate. The 2 MAJORs are **pre-execution
precondition/STOP-set gaps**, not wrong values or procedure: (1) the unit does not carry the accepted code review's
C3 (Ada Linux/CPU test selections) among its pre-U2 gates and does not cite the accepted code review/fixed report;
(2) the STOP/no-retry set is incomplete (timeout/OOM, CUDA-IPC error, non-finite metric, synthetic, gate/kit/data/env
mismatch, disk) and the co-tenant / fresh-authorization / one-smoke wording is ambiguous. Both are text additions
that add the missing precondition/STOP rules and change no measurement identity, kit byte or quoted value. **No execution until C1–C5 are
applied to the unit/launch notes; C6–C8 are satisfied in the result/execution.**

**External-state note (not a unit finding).** The one isolated Ada smoke attempted on 20 Nov
(`ar_cond7a_smoke_20261120T223548Z/`) is a **STOP caused by an external co-tenant CUDA OOM**, not a U2 result: the
card was verified idle at the 22:35:48Z launch, another user's job (zihaozhao, 9 processes, ≈42,570 MiB ≈41.6 GiB)
started ≈3 min later, and the baseline evaluation OOMed in the causality probe (1 executed baseline record +
refused `s001`; `CHECKLIST_E_PASSED` not reached; no retry). The unit correctly counts this as an external STOP and
requires a pre-U2 isolated smoke to pass. A new smoke needs **fresh coordinator authorization** and a card guaranteed
idle for the whole run (AR smoke result §6.5; U4 census R5 n4). The U2 may not start until that fresh smoke passes.

## 1. Authority, inputs and the unit's checks (read-only, verified in this session)

- **PLAN rows** on the worktree's tree and on `origin/main` **`df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`**
  (`docs/r1/PLAN.md`): `R1-TRACKG-G0-GO:1258` (U2 per node, one node per unit, each unit independently reviewed,
  ENGINEERING_ONLY, re-check idle card/sharing/Paper A gate each time, no noise floor/D21/D28),
  `R1-TRACKG-LICENCES:1269`, `R1-TRACKG-PORT-DECISIONS:1289` (incl. **(4) node timeout = census baseline × 3; a
  timeout is the proposal's failure, not an infrastructure rerun; census on Python 3.12**),
  `R1-HARNESS-ISOLATION:1290`, and **`R1-TRACKG-AR-COND7:1317`** (option A: CUDA IPC removed from the result path;
  `torch.cuda.init()` in `cuda_open`; **`effective:true` with no waivers**; kit pins and `frozen_pin_sha256` updated;
  **one isolated smoke runs, then the U2 unit**; the logits-transfer slowdown measured and disclosed).
- **Port report** `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md`, sha256
  **`78d354b884ef0f13c92768d75662d7e1bf9ec5b2426e59f42e3d721d5e6f6183`**, §2 (how every node runs) and §7
  (experiment-agent steps). §7 step 3 says to check every run record and — for autoresearch — that `effective` is
  false by design with `exceptions == ["shared_dev_shm"]`; §2's autoresearch row still describes the old
  CUDA-IPC-on-GPU path. **Both are superseded by COND7 option A** (see m1); the unit's own isolation requirement is
  the correct COND7 one.
- **Accepted option-A code review** `docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md`, sha256
  **`261a03e9afb5921f6afdcc0979e83122d1f8cbaef85d6cf723c21ded8db66cae`** — **ACCEPTED for the code change: 0
  BLOCKING, 1 MAJOR (report-only M1), 6 MINOR; conditions C1–C6.** The MAJOR M1 (slowdown disclosure ~80×
  understated: the real config is 640 validation + 3 probe + 1 repeat = **644 requests/run** of a 1 GiB buffer,
  ≈640 GiB one-way, ≈**97–161 s/run**, likely **2.4–3.4×** the 17 Nov B1 `67.901 s`) is report-only; C2 is the one
  Ada smoke, C3 the Ada Linux/CPU test selections, C6 says the **U2 unit may start only after C1–C3 and the passing
  isolated Ada smoke**.
- **Fixed code-unit report at the branch tip** `docs/r1/reports/trackg_g0_20261117/TRACKG_AR_COND7A_CODE_UNIT_20261120.md`,
  sha256 **`370782abf2c14850c9b56f70789df51bee3e332ac37bcf7a82134366081df0a8`** (336 lines; §11 disposition of
  M1/m1–m6; §8 corrected to the real 644-request configuration). Evidence captures
  `..._captures/SHA256SUMS` sha256 **`49d4c3a89339fa43f0654d708faf5ba4c89acc9c0836f0bdbbeff3b75e5cbd8d`**
  (**17/17 OK**, `shasum -a 256 -c`, rc 0, verified in this session).
- **Accepted isolation fix** `5403392e` (merge `2e65922`), review
  `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha256 **`c8e468c76af682e48d6a56607835e4a974e359f78be86333e6d9f37c9fc1ca36`**
  (ACCEPTED); its C3 requires the logits-transfer decision + `cuda_open` init fix, which is this branch.
- **Prior U2 pattern/standards:** `docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` sha
  **`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`** (ACCEPTED; mR1–mR11, incl. the one-line
  launch command, the 1 s whole-smoke VRAM sampler upper bound, both pins, the full result-record standard);
  `docs/r1/reviews/TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md` sha
  **`81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51`** (ACCEPTED, C1–C7); the accepted 17 Nov
  AR result `TRACKG_U2_AR_RESULT_20261117.md` sha **`a6ddfbd0c6c4d5d2905abe798495564a39ea91b87ebd623da5d6fe34a1b6ca8b`**;
  the 20 Nov AR smoke STOP result `U2_ISO_AR_COND7A_RESULT_20261120.md` sha
  **`bcb74efc99f87bcd43a18b9deb56303c8a28774e0bd312e3ba78a72069096bdc`**; the U2 summary
  `TRACKG_U2_ISO_RESULTS_20261119.md` sha **`ea512177241ee76889ab28a5e933655bb658ecad558b85d47c4682cddbee3876`**;
  the U4 census review R5 `TRACKG_U4_CENSUS_REVIEW_R5_20261120.md` sha
  **`9c604f1b1220652cb3ccc109e0d85863b6a9e34ac02237b5ff57070fc3cc6b91`**; U1 licence
  `U1_LICENCE_AVAILABILITY_20261117.md` sha **`70d54b71c56e5318ad91135e6b5bec7aad2ee3694917800847d3158a6d8fa7b1`**.

## 2. Kit, tip and pins — PASS (independently reproduced)

- Branch `mac-trackg-iso-ar-cond7a-20261120` @ **`73303380197477df971e865440d0ae11135fe1b3`**, worktree
  `.claude-worktrees/harness_ar_cond7_20261120`, tracked-clean; `448f6820…` is an ancestor; 4 linear commits, no
  merges: `0e0b820` (7-file code/test/spec/manifest change), `6f235c4` (report edit), `13786d1` (captures),
  `7330338` (report M1/m1–m6 fix); `origin/mac-trackg-iso-ar-cond7a-20261120` = `7330338` (pushed). The unit's tip
  and "HEAD==tip and tracked-clean at launch; wrong/dirty kit = STOP" are correct.
- **Pins recomputed in this session with the kit's own loader/function** (`load_trackg_node_spec` +
  `frozen_file_hashes` + `sha256(json.dumps(pin, sort_keys=True))`, no writes, `PYTHONDONTWRITEBYTECODE=1`):
  committed-file **`147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`** (20 entries) and, with the
  deployed `data -> /home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens` link, deployed
  **`069e987ac71a8ff30db7a28b7410778a4a8211aa3ecff00e23437498f2e9d2ed`** (21 entries). Both match the unit
  (`:13-15`), the code report §5, the smoke `prep/pins_committed.txt`/`prep/pins_deployed.txt` and the executed
  baseline record (`frozen_pin_sha256 = 069e987a…`). The unit's convention is correct: the two are recorded
  separately and **the census uses the committed-file pin**.
- Spec `raw_sha256` **`5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`** (recomputed), spec file
  sha `5bdce00a…`, representative-edits manifest `55f2666a…`; node files `run_fixed_budget.py` `58d80b52…`,
  `ar_worker.py` `65a4927c…`, `ar_isolated.py` `3ba34c67…`, `LICENCES.md` `1104c38a…` — all match the accepted code
  report/review table.
- **Option-A path requirement — PASS (static).** AST scan of `run_fixed_budget.py` and `ar_worker.py` for
  `{cuda_share, cuda_open, _share_cuda_, _new_shared_cuda, bind_cuda}` → **NONE** (re-run in this session; matches
  the smoke `prep/cuda_ipc_scan.txt`). The unit requires the same static check (it names four of the five
  identifiers; `_new_shared_cuda` is reached only through `cuda_open`, which is also absent) and the worker→parent
  CPU `SharedBuffer` path. The metric is still parent-only (code review §3), so the option-A condition is met by
  the accepted change.

## 3. Data, environment and licence/provenance — PASS

- Data `/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens` outside the repo; manifest
  **`ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`** (13 files, 963 M) — matches the accepted
  17 Nov AR result, the 20 Nov smoke capture (`prep/data_manifest.txt`, `prechecks.txt` re-check) and the unit.
- Env `envs/torch312`: Python **3.12.16**, torch **2.6.0+cu124**, `uv pip freeze` **77 lines, sha
  `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** — the accepted isolation-check freeze
  (the 17 Nov AR run used the earlier `dea8a9df…`; the unit says "at the accepted isolation checks; re-record",
  correct).
- Licence/provenance: the unit cites `R1-TRACKG-LICENCES`; U1 §2 and the node `LICENCES.md` confirm autoresearch's
  code is **MIT declared in the README only** (no LICENSE file; GitHub API `license: null`), the ported code is the
  harness's `nodes/autoresearch-macos` fork (`fb405e1`/`d075bb3`), and the climbmix HF card's MIT is the uploader's
  assertion with undocumented corpus provenance; "data prepared by us" is correct. (Detail gap → m8.)

## 4. Isolation — PASS (the unit requires exactly the COND7 expectation)

The spec (accepted at the tip) has `isolation.shared_dev_shm: false`; the runner computes
`exceptions = ["shared_dev_shm"] if shared_dev_shm else []` and
`effective = not waivers and not exceptions and euid != 0 and cgroup is not None and sandbox is not None`. The unit
therefore correctly requires, on every executed record, **`effective:true`, `waivers {}`, `exceptions []`, private
`/dev/shm` (`shared_dev_shm:false`)**, plus log/result-channel/cgroup checks, and states that an effective-false or
waiver record is a STOP. This is what the 20 Nov executed baseline record already showed
(`effective:true`, `waivers {}`, `exceptions []`, `worker_sandbox.shared_dev_shm:false`, `cgroup.kill` with
`empty_after:true`), and it is the PLAN COND7 requirement — **not** the stale port-report §7 autoresearch rule (m1).

## 5. Host, GPU, gate and cgroup command — PASS with record residuals

- The unit requires the Paper A three-check gate clear immediately before launch, **one exclusively idle GPU (no
  other user's compute app for the whole smoke)**, ≥40 GiB free at launch, UUID and cpuset recorded, 8 GiB delegated
  cgroup, and "never launch on a shared card". It explicitly records the 20 Nov attempt as an **external STOP**, not
  a unit result. This is the right response to the observed failure (idle card verified, co-tenant appeared ~3 min
  later).
- The launch command is the accepted construction: outer `systemd-run --user --scope -p Delegate=yes -p
  MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`; **inside the scope** `cd <kit>`, `CG=$(cut -d: -f3
  /proc/self/cgroup)`, `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `echo scope_cgroup=…`,
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, env `bin` first on `PATH`, `VIRTUAL_ENV`, `CUDA_VISIBLE_DEVICES=""`,
  `AR_TRACKG_DATA_ROOT=…`, `taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node
  autoresearch_fixedtokens --gpu-uuid <UUID> --cpus <cpus> --memory-limit "external: systemd-run --user --scope -p
  MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo> --provisional-timeout 1800`; the
  unit says "**One physical line**" and the probe `memory.max=8589934592`, `memory.swap.max=0`. The module, flags and
  defaults exist at the tip (`tests/trackg/port_smoke_gpu.py`: `--node`, `--gpu-uuid`, `--cpus`, `--memory-limit`,
  `--runs-root`, `--provisional-timeout 1800`); the `--memory-limit` value equals the failed smoke's recorded
  `limits.external_limit`. Residuals: probe read-path and mismatch STOP (m6), GPU-floor basis/watcher floor (m2),
  concrete runs-root (m11).

## 6. Run/record expectation — PASS on identity, MINOR on wording/fields

- **8 executed + refused `s001`, `CHECKLIST_E_PASSED`** is correct for this node: the smoke runs baseline, frozen
  diff (refused), broken diff, first edit, then E1–E4 on the baseline and a same-seed second baseline = 8 executed +
  1 refused; `check_smoke` asserts baseline ok, frozen `not_run_refused`/`scope_violation`, broken divergent,
  `killed_with:null`, per-edit `applied`/`ok`, and the B2 repeat value equal to the baseline value, then
  `port_smoke_gpu` prints `CHECKLIST_E_PASSED`.
- **B1/B2** — B1 is `s000_baseline`'s `elapsed_seconds_info_only` / `outcome.value` (`val_bpb`, 6 decimals, from
  `AR_METRIC val_bpb=`); B2 the same-seed repeat. The unit's "metric finite and B2 within `CAUSAL_ATOL`" mis-states
  the kit check: the B2 **outcome value must be exactly equal** (`check_smoke` asserts `==`), while `CAUSAL_ATOL`
  governs the parent's logits-repeat check (exit 10) and the causality probe (exit 9, `AR_INFO
  causal_probe_max_change`). (m3/m12.)
- **Timeout** — node timeout = 3 × B1 (port decision (4)); `--provisional-timeout 1800` is the smoke's provisional
  per-run limit. Correct.
- **Slowdown** — the unit requires measured values against the 17 Nov un-isolated B1 `67.901 s` and `564 s` smoke,
  per-run and whole-smoke, replacing the code report's `97–161 s`/`2.4–3.4×` estimate, and notes the ~1 GiB/request
  CPU transport. The 17 Nov comparison is like-for-like on data manifest (`ab7186d2…`), seeds (8001/8001) and full
  budget (32,768,000 tokens), with the training phase unchanged; per-request timing has no timer in the code
  (the failed smoke's `slowdown.json` labels its derived surrogate invalid), so the measurement method/location
  must be stated (m7). The 20 Nov failure produced **no** valid slowdown measurement — the unit must obtain it from
  a clean smoke.

## 7. STOPs, no-retry and the smoke precondition — the main gap (MAJOR-2)

The unit has: wrong/dirty kit = STOP (`:12`), effective-false/waiver record = STOP (`:28`), co-tenant arriving =
external STOP, not U2, "do not retry on a shared card" (`:46-47`). It is missing: an explicit **timeout/OOM STOP**
with "a timeout is the proposal's failure, not an infrastructure rerun" (port decision (4)); **CUDA-IPC-error /
non-finite-metric STOP**; **synthetic-marker STOP**; **gate/kit/data/env/manifest/freeze mismatch STOPs**; **disk
< 50 GiB STOP**; and a general **"one smoke only / no retry of a unit failure"** rule. The co-tenant wording is also
ambiguous: an external co-tenant STOP is not a retry of the unit, but a *new* smoke needs **fresh coordinator
authorization** (AR smoke result §6.5; census R5 n4) and a card guaranteed idle for the whole run — the unit says
only "do not retry on a shared card". These are added as C2.

## 8. Findings

| # | severity | where | finding |
|---|---|---|---|
| **MAJOR-1** | **MAJOR** | `unit:3-4`, `:11`, `:54-56` | **Pre-U2 gate incomplete.** The unit's status gates only on "fresh independent review + pre-U2 isolated smoke passes". The accepted option-A code review (sha `261a03e9…`) **C6** says the U2 may start only after **C1–C3 and the passing isolated Ada smoke**; **C1** is fixed at the tip, but **C3** (the Ada Linux/CPU test selections: `tests/trackg` with the 19 Linux-only isolation tests *included*, in particular `test_dev_shm_is_private_unless_the_node_opts_out` and `test_shared_buffer_is_sealed_against_resizing`, and the full `test_port_autoresearch.py` including the 18 skipped wrapper/smoke tests (torch/pyarrow/rustbpe), no new failures vs `448f682`) is neither required nor recorded anywhere in the 20 Nov smoke record. The unit also does not cite the accepted code review (`261a03e9…`) or the fixed code report (`370782ab…`). |
| **MAJOR-2** | **MAJOR** | `unit:28`, `:42-47` | **STOP/no-retry set incomplete and co-tenant/one-smoke wording ambiguous.** No explicit timeout/OOM STOP or "proposal failure, not infrastructure rerun" (R1-TRACKG-PORT-DECISIONS (4)); no CUDA-IPC-error, non-finite-metric, synthetic-marker, gate/kit/data/env mismatch or disk STOP; no general "one smoke only / no retry" rule. "do not retry on a shared card" leaves open an automatic retry on an idle card; a **new** smoke after the external 20 Nov STOP needs fresh coordinator authorization (AR smoke result §6.5; census R5 n4) and a card guaranteed idle for the whole run. |
| m1 | MINOR | `unit:4-6`, `:5`, `:28`, `:48-50` | **Cited port report §2/§7 is stale for autoresearch** (§7 step 3 says `effective` false by design with `exceptions == ["shared_dev_shm"]`; §2 says CUDA IPC on a GPU); both are superseded by COND7 option A. Cite the path/sha `78d354b8…` and state the supersession, and require a **COND7-aware run-record verifier**. The kit-update capture tools still encode the old rule: `TRACKG_ISO_KIT_UPDATE_20261119_captures/scripts/verify_records.py` (`6104fd5b…`: "autoresearch may be effective false only with exceptions == ['shared_dev_shm']") and `collect_smoke_summary.py` (`21624f86…`: same rule) — on the 20 Nov record they produced the **false** findings "autoresearch exceptions are not ['shared_dev_shm']" and "ar exceptions []", while the smoke's own `scripts/verify_ar_cond7a.py` has the correct COND7 expectation. A successful U2 record must not be falsely STOPped by the stale tools. |
| m2 | MINOR | `unit:18` | ≥40 GiB floor has no stated basis, and the 20 Nov launch tooling's floor was **8 GiB** (`watch_and_run_cond7a.sh`, `run_ar_cond7a.sh` headers: "idle GPU >=8 GiB/no app"). State the basis (17 Nov measured worker peak `5,211.3 MB`; option-A transient host/VRAM ~1 GiB memfd + ~1 GiB snapshot; the failed smoke's parent 4.21 + worker 3.42 GiB at the probe) and require the qualification/watcher floor to be **40 GiB**, not the 8 GiB default, with the free-VRAM/co-tenant census at launch. |
| m3 | MINOR | `unit:42-43` | "B2 within `CAUSAL_ATOL`" mis-states the kit: the smoke's B2 **outcome value must equal B1 exactly** (`check_smoke`); `CAUSAL_ATOL` applies to the parent's logits repeat (exit 10) and causality probe (exit 9, `AR_INFO causal_probe_max_change`). Record both. |
| m4 | MINOR | `unit:48-50` | "sampler/labels if used" is too weak: the accepted U2 standard (R3 M1) requires the 1 s `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` sampler for the whole smoke, with its maximum recorded as a **whole-smoke upper bound over the used GPU(s), including co-tenants, not a per-run peak** (the 20 Nov smoke already did this: max 48,128 MiB). Make it mandatory. |
| m5 | MINOR | `unit:48-50` | Result-field list is below the accepted standard: add setup command/log path+sha, the CPU-masked/Ada static-test command/result (with C3), `process.returncode`/`timed_out`, `determinism.not_forced`/`shim_loaded`, per-run `run_record.json`/`run.log`/`result_channel.txt` paths+sha, one JSON line per run, node-spec + representative-edit manifest shas, result-file name/path/sha, gate JSON path/sha/UTC, env-freeze-mismatch STOP, data manifest file count/size/read-only + the `AR_DATA manifest_sha256=… files=13` line, disk `du`/`df` before/after + <50 GiB STOP, cgroup `memory.peak`/`memory.events` (oom/oom_kill) and cap mechanism, host/kernel/driver/boot, `kit.txt` (HEAD==tip, tracked-clean), resolved invocation, and `log_intact`/result channel/`cgroup.kill`. |
| m6 | MINOR | `unit:41` | Probe: state how `memory.max`/`memory.swap.max` is read after start (via the echoed `scope_cgroup=` path or inside the scope while the smoke runs), and add an explicit **STOP if the bytes are not `8589934592`/`0`** (the unit states the expected values but no mismatch STOP). |
| m7 | MINOR | `unit:44-47` | Slowdown: state **where** the measured per-run and whole-smoke values are recorded (U2 result) and that the code report §8 estimate is replaced/annotated (C2/C6 of the code review); the code prints no per-request transfer timer, so state the method for any per-request number (log timestamps / instrumentation; a code change would need its own review) or record per-run only explicitly; label the `67.901 s`/`564 s` reference as the 17 Nov **un-isolated kit/env** baseline with identical data manifest, seeds and budget (training path unchanged). |
| m8 | MINOR | `unit:23-24` | Licence/provenance detail: record the ported-code provenance (harness `nodes/autoresearch-macos` fork `fb405e1`/`d075bb3`; upstream karpathy HEAD `228791fb…`; MIT **declared in README only**, no LICENSE file, GitHub API `license:null`), the attribution string, and the climbmix HF card's MIT being the uploader's assertion; record the data `AR_DATA` line/source revision (`915333b4…`) and manifest file count/size/read-only. |
| m9 | MINOR | `unit:13-15` | Pins: record both as **full 64-hex** and state they are **re-read at launch** from the kit loader/setup (the unit embeds the full committed value and the deployed prefix `069e987a…`; keep values as expected-only, never copy a truncated prefix); the deployed pin is target-dependent (here `069e987a…` for `/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens`); do not compare a run record to `147f0d35…` directly; no other node's pin. |
| m10 | MINOR | `unit:3-6` | Citations/scope residues: cite the accepted code review `261a03e9…`, the fixed code report `370782ab…`, the isolation-fix review `c8e468c7…`, the port report path/sha `78d354b8…`, the R3 review `99daf16d…`, the 17 Nov AR result `a6ddfbd0…`, the 20 Nov STOP result `bcb74efc…`, the U2 summary `ea512177…` and census R5 `9c604f1b…`; state the authority main/commit; "**no push**" not only "no force push"; no other host beyond HTCondor/deepthought (TASL-7/TASL-2); no secrets; no resume (an interrupted unit re-runs whole from a new runs-root); explicit exclusion of other nodes/T1. |
| m11 | MINOR | `unit:33-41` | Name a concrete runs-root outside the repo (e.g. `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_autoresearch_<UTC>`), state that a **fresh** worktree at `7330338` is used (or the clean 20 Nov worktree reused) with existing worktrees left untouched, and record the resolved invocation. |
| m12 | MINOR | `unit:42-43` | Baseline semantics/sanity: B1 = `s000_baseline` `elapsed_seconds_info_only` and `outcome.value` (val_bpb); B2 = same-seed repeat (exact equality); record the worker `AR_INFO peak_vram_mb` and the parent peak; sanity-check the training phase (500/500 steps, `AR_TOKENS consumed=32768000`, data manifest `ab7186d2…`, no `synthetic` marker). |
| m13 | MINOR | `unit:48-50` | Record the reviewed unit sha **`3bb015a1…`** and preserve the executed amended unit copy with the result; the unit is untracked at review time. |
| m14 | MINOR | `unit:53-56` | Review-conditions line: require the result reviewer to check the **COND7** isolation expectation and the COND7-aware verifier outputs, and to preserve references to the 20 Nov external STOP (no retry; a new smoke needs fresh authorization). |

**BLOCKING: none.** No wrong kit tip, pin, data hash, spec hash or command element was found; no scope/authority
violation; no CUDA-IPC path remains; the isolation expectation is the correct COND7 one.

## 9. Conditions

All conditions are text/record additions; none changes the procedure, scope, measurement identity, STOP set's
intent, or a kit byte. **No execution until C1–C5 are applied to the unit/launch notes; C6–C8 are satisfied in the
result/execution.**

- **C1 (MAJOR-1 — the pre-U2 gate).** Add to the unit's status and launch notes: the U2 may start only after
  (a) the accepted code review's **C1–C3** are closed — C1 fixed at the tip `7330338` (report M1/m1–m6), **C3
  recorded**: the Ada Linux/CPU test selections (`tests/trackg` with the 19 Linux-only isolation tests included,
  incl. `test_dev_shm_is_private_unless_the_node_opts_out` and `test_shared_buffer_is_sealed_against_resizing`, and
  the full `test_port_autoresearch.py` incl. the 18 skipped wrapper/smoke tests) with no new failures vs `448f682`, with
  command/mask/interpreter/result/log sha; (b) a **fresh clean isolated smoke passes** (below); and (c) this review's
  acceptance. Cite the accepted code review `261a03e9…` and the fixed code report `370782ab…`.
- **C2 (MAJOR-2 — STOPs and no-retry).** Add the full STOP set: co-tenant arriving during the run = **external
  STOP** (preserve, not a U2 result; no automatic retry; a new smoke needs fresh coordinator authorization and a card
  guaranteed idle for the whole run — AR smoke result §6.5, census R5 n4); timeout/OOM, any executed record not
  `effective:true`/`waivers {}`/`exceptions []`, CUDA-IPC error, non-finite/absent metric, synthetic marker,
  wrong/dirty kit, gate not clear, data/env/manifest/spec/pin mismatch, disk < 50 GiB = **STOP, no retry**; a
  timeout is the proposal's failure, not an infrastructure rerun (R1-TRACKG-PORT-DECISIONS (4)). State "one smoke
  only for this node" and that the 20 Nov STOP is external, consumed the smoke, and is not U2 evidence.
- **C3 (m1 — stale §2/§7 and verifier).** Cite the port report path/sha `78d354b8…`; state §2/§7's autoresearch text
  is superseded by COND7 option A; require a COND7-aware record verifier (the `verify_ar_cond7a.py` pattern, sha
  recorded) and explicitly do **not** apply the kit-update `verify_records.py`/`collect_smoke_summary.py`
  autoresearch rule (`effective:false` / `exceptions ["shared_dev_shm"]`), which already produced a false STOP on
  the 20 Nov record.
- **C4 (m2, m6).** State the ≥40 GiB basis and require the qualification/watcher floor to be 40 GiB (not the 8 GiB
  default), with the launch free-VRAM/UUID/cpuset/co-tenant census; add the probe read-path and an explicit
  `8589934592`/`0` mismatch STOP.
- **C5 (m3, m4, m5, m12).** Fix the B2/`CAUSAL_ATOL` wording (exact B2 outcome equality; logits repeat/causality
  within `CAUSAL_ATOL`); make the 1 s whole-smoke compute-app sampler mandatory with the upper-bound label; complete
  the result-field list (m5); state B1/B2 definitions and the training-phase sanity checks.
- **C6 (m7, m8, m9, m11, m13).** Record the measured slowdown location/method (per-run; per-request method or an
  explicit per-run-only statement) and replace/annotate the code report §8 estimate; add the licence/provenance
  detail; record both pins as full 64-hex and re-read at launch; name the concrete outside-repo runs-root and the
  fresh worktree; record the reviewed unit sha and preserve the executed amended copy.
- **C7 (m10).** Add the citation/scope residues: accepted code review/report, isolation-fix review, port report
  path/sha, R3 review, 17 Nov AR result, 20 Nov STOP result, U2 summary, census R5; authority main/commit; "no push";
  no other host (TASL-7/TASL-2), no secrets, no resume; explicit other-node/T1 exclusion.
- **C8 (execution rule).** One node only (`autoresearch_fixedtokens`), one fresh smoke, ENGINEERING_ONLY with no
  evidence/noise/D21/D28 and no T1; no deletion/push; no HTCondor/deepthought; the U2 runs only after a fresh clean
  isolated smoke passes (the 20 Nov co-tenant STOP is external and is not a U2 result); the U2 result carries the
  measured slowdown, the deployed/committed pin convention and the COND7 isolation fields; acceptance of this unit
  authorises no other node, no T1 label/sweep, and no cross-node comparison.

## 10. Verdict

**ACCEPTED — 0 BLOCKING, 2 MAJOR, 14 MINOR, conditional on C1–C8.** The unit is substantively correct and the
quoted identities are independently verified: one node, ENGINEERING_ONLY; kit `mac-trackg-iso-ar-cond7a-20261120`
@ `7330338` (`448f682` ancestor, 4 linear commits, tracked-clean, pushed); committed pin
`147f0d35…` (20 entries) and deployed pin `069e987a…` (21 entries) reproduced with the kit's own loader/function;
spec `5c1bdf3d…`/`5bdce00a…`; data manifest `ab7186d2…` (13 files, 963 M); env `d2e70fe4…` (Python 3.12.16, torch
2.6.0+cu124); option-A result path with **no CUDA-IPC API use**; isolation `effective:true`/`waivers {}`/`exceptions
[]`/private `/dev/shm`; the accepted inside-scope cgroup command with the 8 GiB/0 probe, `taskset`, outside-repo
runs-root and provisional 1800 s; exclusive-idle GPU with a ≥40 GiB floor; 8 executed + refused `s001` +
`CHECKLIST_E_PASSED`; B1/B2 `val_bpb`, 3 × B1 timeout; the measured-slowdown requirement against the 17 Nov
`67.901 s`/`564 s` and the corrected `97–161 s`/`2.4–3.4×` estimate; the explicit external-STOP handling of the
20 Nov smoke. The 2 MAJORs are pre-execution precondition/STOP-set gaps (C1/C2), not wrong values; the 14 MINORs
are the accepted record/citation classes. **No execution until C1–C5 are applied and a fresh clean isolated smoke
passes; the 20 Nov co-tenant OOM is an external STOP, not a unit result, and a new smoke needs fresh
authorization.**

## 11. Attestation and read-only command record

This review is the only file written (uncommitted; no unit/code/kit edit, no commit, no push, no deletion). I did
not run the smoke or any GPU/U2/census job, did not log in to Ada, and did not touch HTCondor, deepthought,
TASL-7/TASL-2. Read-only operations (21 Nov 2026, Europe/Berlin): `pwd`; `git -C ops-tasl-20261116 rev-parse HEAD`
(`5bc4e5c0f0d8874f765d7ba81fec8cfef8beceea`) / `origin/main`
(`df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`) / `status --porcelain` (unit untracked; no other changes);
`git show origin/main:docs/r1/PLAN.md` rows `R1-TRACKG-G0-GO:1258`, `R1-TRACKG-LICENCES:1269`,
`R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`, `R1-TRACKG-AR-COND7:1317`; `git -C
harness_ar_cond7_20261120 rev-parse HEAD` (`7330338`) / `git status --porcelain` (clean) / `git log 448f6820..HEAD`
(4 commits) / `git merge-base --is-ancestor 448f6820 HEAD` / `git rev-parse
origin/mac-trackg-iso-ar-cond7a-20261120` (`7330338`); `sha256sum` of the reviewed unit (`3bb015a1…`, 56 lines,
4,489 bytes), the code review (`261a03e9…`), the fixed code report (`370782ab…`), the isolation-fix review
(`c8e468c7…`), the port report (`78d354b8…`), the R3 review (`99daf16d…`), the HousePrice R2 review (`81580eec…`),
the 17 Nov AR result (`a6ddfbd0…`), the 20 Nov STOP result (`bcb74efc…`), `RESULT_STATUS.txt` (`62313f1d…`), the
U2 summary (`ea512177…`), census R5 (`9c604f1b…`), U1 licence (`70d54b71…`) and the node `LICENCES.md`
(`1104c38a…`); `shasum -a 256 -c SHA256SUMS` in `TRACKG_AR_COND7A_CODE_UNIT_20261120_captures` (**17/17 OK, rc 0**)
and in `ar_cond7a_smoke_20261120T223548Z` (**1800/1800 OK**, SHA256SUMS sha `231d388e…`); independent recomputation
(no writes, `PYTHONDONTWRITEBYTECODE=1`) of the committed pin (`147f0d35…`, 20 entries), the expected deployed pin
with `data: link:/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens` (`069e987a…`, 21 entries), the spec
raw sha (`5c1bdf3d…`) and the AST CUDA-IPC scan (NONE for both result-path files) using the kit's own
`load_trackg_node_spec`/`frozen_file_hashes`; reads of the unit, the code review and fixed code report, the port
report §2/§7, the 20 Nov smoke STOP record (`prep/pins_*`, `prep/data_manifest.txt`, `prep/cuda_ipc_scan.txt`,
`summary.json`, `verify_records.json`, `verify_full.summary.txt`, `slowdown.json`, `kit.txt`,
`invocation_inner.sh`, `scripts/`), the 20 Nov result, the 17 Nov AR result/review, the U2 summary, census R5, the
R3/Breakout-adjacent reviews, the kit `port_smoke_gpu.py`/`port_support.py`/`run_fixed_budget.py`, U1 §2/§7 and the
node `LICENCES.md`. No live Ada host state is claimed beyond what those accepted records and captures show.
