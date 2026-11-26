# U2 census retry — `mlgym_titanic` (MLGym Titanic) on TASL-2, 25 November 2026 — **RESULT: PASS**

**Verdict: PASS — the one authorised clean retry ran alone on an idle host (CPUs 8–11 P-cores, no GPU, no GPU
lease, delegated 8 GB / swap 0 scope), completed all nine smoke runs at the full 150,000-step budget, printed
`CHECKLIST_E_PASSED mlgym_titanic`, and the postflight reports `failed_checks: []` (all 64 recorded checks
true). B1 and B2 are bit-identical (val 0.775281, sealed test 0.763158), the kit-accepted checklist-E values are
reproduced digit-for-digit, and the census basis is set: `measured_run_seconds = 156` (slowest census run E3
155.965 s) with `timeout = 468.0 s` (3×, inside the chunk schema `(0, 300]`). The prior failed attempt B and the
aborted attempt A are preserved untouched; nothing was deleted and nothing was pushed.** Prepared by the retry
runner (a delegated agent, AI-assisted) for the lead; ENGINEERING_ONLY — no GPU, no G.1b/evidence file, no data
copied into any repo. Captures are beside this file under `captures/titanic_u2_retry_20261125/` with their own
`SHA256SUMS`.

## 0. One-line result

| item | value |
|---|---|
| node / kit | `mlgym_titanic`, `/home/dowling/r1_trackp/wt/titanic-20261125` @ `3a67042ba7e4211feb9681524f3879643c8cf635`, branch `mac-trackg-titanic-20261125` |
| retry evidence root (outside repo) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_RETRY` |
| preflight | PASS 14:08:25Z (HEAD `3a67042b…`, pins/data/env re-verified, GPU hidden, no lease) |
| one retry launch (UTC) | **14:08:37Z → 14:26:58Z** (smoke wall 18 m 21 s), unit `u2-titanic-census-20261125T1408Z.scope`, single scope invocation |
| smoke | reviewed `python -m tests.trackg.port_smoke_gpu --node mlgym_titanic`, full 150,000-step budget, seeds 8001/8001; launch rc **0**, `CHECKLIST_E_PASSED mlgym_titanic` |
| **B1 / B2** | val_accuracy **0.775281 / 0.775281**, sealed test_accuracy **0.763158 / 0.763158**; determinism B2 == B1 **True** |
| edit runs | s003 = E1 = 0.803371 / 0.772727; E2 0.775281 / 0.751196; E3 0.792135 / 0.784689; E4 0.792135 / 0.746411; s002 genuine `non_finite_loss` divergence; s001 refused `scope_violation` |
| isolation (all executed) | effective `true`, waivers `{}`, exceptions `[]`, frozen files checked 16 / changed `[]`, ptrace_scope 1, worker sandbox present, cgroup killed clean |
| determinism | settings forced except `dataloader_workers` (expected torch-node list); torch 2.6.0+cu124; no GPU ids, `CUDA_VISIBLE_DEVICES=""` |
| pins/data/env | committed pin `0368a73d…`, deployed pin `4c0399d9…`, edits manifest `fd464c6e…`, data manifest `c8ccedd0…`, torch312 freeze `d2e70fe4…` (77 pkgs, Python 3.12.16), node spec `059fd0d5…` |
| census basis | `measured_run_seconds` **156** (slowest E3 155.965 s; basis s000/B2/E1/E2/E3/E4), `timeout` **468.0 s** (3×, schema `(0, 300]`), provisional 1800 s recorded, no timeout/kill |
| resources | scope `memory.peak` **643,932,160 B** of `memory.max` 8,589,934,592 B, swap max 0; per-run cgroup peaks 596,221,952–596,676,608 B; per-run VmHWM 606,167,040–620,183,552 B; runs root **6,133,455 B**; data root 97,270 B; home avail after 371,345,485,824 B; no OOM |
| GPU / policy | no GPU, no lease (`gpu0.lock` untouched, not held); nothing deleted, nothing pushed, no evidence/G.1b file written |
| captures `SHA256SUMS` | sha256 **`feb9518338814d8b3522e58e5ec044ea3c5faba8e439a60c8eae4569389d207d`** (67 files; remote `sha256sum -c` rc 0 and local `shasum -a 256 -c` rc 0) |
| prior failed attempt B (kept) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B` — STOP; captures `SHA256SUMS` sha256 `a6f35989a1dc11d5e1d1432d1149e7d8bed1b2cfe02c151c35616280b7627554` (89 files, `sha256sum -c` rc 0), untouched |
| prior aborted attempt A (kept) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted` — untouched |

## 1. Authorisation and why a retry was made

The earlier TASL-2 U2 smoke of this kit (attempt B, one launch 13:04:10Z–13:16:01Z on the same CPUs 8–11) STOPped
with sporadic native process crashes (E1 killed signal 11, E2 killed signal 4, B2 worker died) while a sibling
U2 smoke shared CPUs 8–11. The same host has since passed a clean Forest Cover U2 smoke on CPUs 8–11
(13:41–13:56Z). At the start of this retry the host had **no smoke process and load average < 1**; no other smoke
ran during it. Exactly one clean retry per kit was authorised, sequentially, with no GPU, no G.1b/evidence, no
deletion and no push. A second STOP would have been preserved and reported with no further retry — it was not
needed: this retry PASSed.

## 2. Prior attempts (kept, not part of this retry record)

- **Attempt A (aborted by lead authorisation, 12:55:25Z–13:03:05Z, CPUs 16–31 E-cores):** CPU-set/schema risk
  (baseline reached step 97,440/150,000 in 458 s, projecting a census run > 300 s, above the chunk schema cap),
  preserved at `…/u2_census_smoke_20261125_attemptA_ecores_aborted`.
- **Attempt B (one launch, 13:04:10Z–13:16:01Z, CPUs 8–11): STOP.** Preflight PASS; s000_baseline 0.775281 /
  0.763158, s003 0.803371 / 0.772727, E3 0.792135 / 0.784689, E4 0.792135 / 0.746411 (identical to the
  kit-accepted values) and s002 a genuine `non_finite_loss`, but E1 was killed by signal 11 (0.532 s), E2 by
  signal 4 (0.660 s) and B2's worker died (exit 1, 1.563 s), so `check_smoke` failed. Preserved at
  `…/u2_census_smoke_20261125B`; its captures verify (`sha256sum -c` rc 0, 89 files) and **no file under it was
  modified after 06:00 PST (14:00Z)** — untouched by this retry. This retry is the authorised clean re-run of the
  same command on the same CPU set.

## 3. Retry binding (preflight PASS 14:08:25Z, then exactly one launch)

| item | value |
|---|---|
| host | TASL-2 (`ssh -o BatchMode=yes portal_zhixu`), Intel Core i9-14900KF, 32 logical CPUs; CPUs 8–11 = P-cores (`Cpus_allowed_list: 8-11`) |
| scope | `systemd-run --user --scope --unit=u2-titanic-census-20261125T1408Z -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`; `AR_TEST_CGROUP_PARENT` = the scope cgroup; `memory.max` 8,589,934,592 B, `memory.swap.max` 0 |
| GPU | none, none leased; `CUDA_VISIBLE_DEVICES=""` (`cuda_device_count_hidden 0`); `~/r1_locks/gpu0.lock` present but not held and untouched; GPU idle before/after |
| env | `/home/dowling/r1_tracks/t1_tasl/envs/torch312` (Python 3.12.16, 77 packages), freeze `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`; `torch 2.6.0+cu124`, numpy 2.5.4, pandas 3.1.1; `PATH` = torch312/bin first, absolute interpreter `…/torch312/bin/python`, `PYTHONDONTWRITEBYTECODE=1` |
| data | `/home/dowling/r1_engineering/titanic_20261125/data/mlgym_titanic`, read-only outside the repo, manifest `c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4` |
| kit | HEAD `3a67042ba7e4211feb9681524f3879643c8cf635` (branch `mac-trackg-titanic-20261125`, base `c025f89a…`); worktree unchanged (only the setup data link untracked) |
| pins | committed `0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086`, deployed `4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107`, edits manifest `fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce`, node spec `059fd0d50059b462…`, frozen entries 16 |
| budget / timeout | steps 150,000 (full, every executed run); provisional timeout 1800 s recorded in every run record |
| runs root | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_RETRY/runs` (outside the repo) |
| scripts | `scripts/` = launch.sh, scope_inner.sh, monitor.py, pins_preflight.py, postflight.py — copied from attempt B; postflight narrative/metadata adapted to this retry, check logic unchanged (see `POSTFLIGHT_NOTE.txt`) |

## 4. The one retry smoke and its result

The module ran once; every executed run used the full budget, CPUs [8,9,10,11], the delegated scope cgroup, no
GPU, and reported `isolation.effective: true` with waivers `{}`/exceptions `[]` and 16 frozen files unchanged:

| run | executed | diff_status | outcome | value (val) | sealed test | elapsed s | iso effective/waivers/exceptions | frozen | killed |
|---|---|---|---|---|---|---|---|---|---|
| s000_baseline (B1) | true | — | ok | **0.775281** | **0.763158** | 138.183 | true / {} / [] | 16 | — |
| s001 | false | refused | frozen-path diff refused `scope_violation` (expected) | — | — | — | — | — | — |
| s002 | true | applied | divergent `non_finite_loss` (expected broken diff) | — | 0.0 | 124.736 | true / {} / [] | 16 | — |
| s003 | true | applied | ok | 0.803371 | 0.772727 | 127.937 | true / {} / [] | 16 | — |
| B2 (repeat B1) | true | — | ok | **0.775281** | **0.763158** | 137.714 | true / {} / [] | 16 | — |
| E1 | true | applied | ok | 0.803371 | 0.772727 | 128.040 | true / {} / [] | 16 | — |
| E2 | true | applied | ok | 0.775281 | 0.751196 | 147.810 | true / {} / [] | 16 | — |
| E3 | true | applied | ok | 0.792135 | 0.784689 | 155.965 | true / {} / [] | 16 | — |
| E4 | true | applied | ok | 0.792135 | 0.746411 | 139.607 | true / {} / [] | 16 | — |

- `launch_rc = 0`, `CHECKLIST_E_PASSED mlgym_titanic`, postflight verdict **PASS**, `failed_checks: []` — all 64
  recorded checks true, including `baseline_ok`, `broken_divergent`, `edit_B2_ok`, all `edit_E*_ok/_applied`,
  `determinism_b2_equals_b1`, `determinism_s003_equals_E1`, `reproduces_kit_checklist_e_values`,
  `determinism_settings_forced`, `determinism_torch_2_6_pinned_env`, `isolation_effective_all_executed`,
  `frozen_diff_refused`, `no_gpu_in_every_run`, `no_gpu_lease_taken`, `full_budget_150000`,
  `provisional_timeout_recorded`, `no_timeout_no_kill`, `result_channel_one_line_each`, `loss_lines_15000`,
  `measured_run_seconds_in_chunk_schema`, `memory_cap_8g_swap0`, `no_oom_kill`, `pin_unchanged`,
  `worktree_unchanged`, `runs_root_outside_repository`, `data_manifest_unchanged`, `single_scope_invocation`.
- **B1/B2 determinism:** val_accuracy 0.775281 = 0.775281 and sealed test_accuracy 0.763158 = 0.763158; the
  repeat baseline (B2) is a record-level identity of B1. s003 and E1 also agree (0.803371 / 0.772727).
- **Determinism settings:** `not_forced = ['dataloader_workers']` (the expected list for a torch node),
  determinism shim loaded, `torch 2.6.0`, pinned env. `cudnn.benchmark=False`,
  `torch.use_deterministic_algorithms(True)` and `torch.set_num_threads` are forced.
- **Kit reproduction:** B1, s003, E1-stub, E3 and E4 match the kit-accepted checklist-E values; s002 is the
  intended non-finite divergence; s001 is the intended frozen-diff refusal.

### Census basis (c2)

`s000_baseline` 138.183 s, `B2` 137.714 s, `E1` 128.040 s, `E2` 147.810 s, `E3` 155.965 s, `E4` 139.607 s ⇒
`measured_run_seconds = ceil(155.965) = 156` (≤ 300, inside the chunk schema `(0, 300]`),
`timeout = 3 × 156 = 468.0 s` (`stop_on_timeout: true`, factor 3.0). s002 and s003 are excluded from the timing
basis by the reviewed postflight (`smoke_records_excluded: ["s002", "s003"]`). The provisional 1800 s smoke
timeout is recorded as such; no run timed out and none was killed.

### Resources

Scope `memory.peak` 643,932,160 B of `memory.max` 8,589,934,592 B with `memory.swap.max` 0 (no OOM kill; memory
events clean); per-run cgroup `memory.peak` 596,221,952–596,676,608 B; per-run worker VmHWM
606,167,040–620,183,552 B; runs root 6,133,455 B; data root 97,270 B (read-only); home available after
371,345,485,824 B; GPU idle and unleased after. No timeout and no runner kill.

## 5. Postflight invocation note (audit)

The preserved postflight helper derives its expected CPU set from `U2_CPUS` (default `16-31`, the E-core set of
aborted attempt A). Its first invocation at 14:27:29Z was made without exporting `U2_CPUS`, so it compared the
runs' recorded `cpu_list` [8,9,10,11] with the default and printed one spurious failed check and a STOP banner;
that was an environment-variable slip in the postflight invocation, not a smoke result (the smoke had already
exited 0 and printed `CHECKLIST_E_PASSED`). It was immediately re-run with the launch's own CPU set
(`U2_CPUS=8-11`) at 14:27:43Z: **PASS, failed_checks []**, and the capture set's `postflight.json` / `summary.json`
/ `summary.txt` are from this authoritative run. Both logs are kept (`postflight.log`, `postflight_rerun.log`)
and the note `POSTFLIGHT_NOTE.txt` is in the capture set. Nothing else was re-run.

## 6. What this establishes

- The `mlgym_titanic` U2 census **PASSes on TASL-2** with the pinned kit/env/data, CPUs 8–11, no GPU: B1/B2
  val 0.775281, sealed test 0.763158, deterministic repeats, checklist-E complete, the kit-accepted values
  reproduced, and the census timing basis set at 156 s / 468 s.
- The prior attempt-B native crashes (E1 signal 11, E2 signal 4, B2 worker death) did **not** recur under the
  clean single-smoke conditions — consistent with the sibling-CPU-contention hypothesis for the earlier STOPs,
  and the earlier suspicion that the failures were run-level rather than kit/data/env level.
- Nothing was deleted or pushed; the prior failed attempt and the aborted attempt A are intact and unmodified.
  No G.1b/evidence file was written and no GPU was used or leased.

## 7. Evidence paths and SHAs

| item | path / sha256 |
|---|---|
| retry evidence root (host, preserved) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_RETRY` (`runs/` 6,133,455 B, `raw/`, `captures/`, `scripts/`, `launch.rc`, `RETRY_PASS.txt`) |
| ops-worktree capture set (this dir) | `docs/r1/reports/tasl_chain_20261122/captures/titanic_u2_retry_20261125/` (67 files + `SHA256SUMS`) |
| captures `SHA256SUMS` | sha256 `feb9518338814d8b3522e58e5ec044ea3c5faba8e439a60c8eae4569389d207d`; remote `sha256sum -c` rc 0 and local `shasum -a 256 -c` rc 0 |
| `summary.txt` / `summary.json` / `postflight.json` | in the capture set; verdict PASS, `utc 2026-11-25T14:27:43Z`, `failed_checks []` |
| console / launch | `captures/launch.out`, `captures/launch_env.txt`, `captures/scope_inner.log`, `captures/smoke_stdout.txt`, `captures/monitor.json` |
| prior failed attempt B (host, untouched) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B`; captures `SHA256SUMS` sha256 `a6f35989a1dc11d5e1d1432d1149e7d8bed1b2cfe02c151c35616280b7627554` (89 files, `sha256sum -c` rc 0) |
| prior aborted attempt A (host, untouched) | `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted` |
| kit-accepted checklist-E smoke (host) | `/home/dowling/r1_engineering/titanic_20261125/captures/smoke/smoke_summary.json` (comparison basis reproduced by this retry) |
| host context: clean Forest Cover U2 (same CPUs) | `/home/dowling/r1_engineering/forestcover_port_20261125/u2_census_smoke_20261125U2` — PASS, `utc 2026-11-25T13:56:56Z` |
