# Track G G.0 U2 raw cost — node `autoresearch_fixedtokens` (isolated kit, option A) — unit (21 November 2026)

**Status: proposed unit; run only after a fresh independent review accepts it and the pre-U2 isolated smoke
passes.** One node only. Authority: `R1-TRACKG-G0-GO`, `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS`, `R1-TRACKG-AR-COND7` (option A), port report §2/§7. ENGINEERING_ONLY census; no
evidence/noise/D21/D28; no T1; no HTCondor/deepthought; no deletion; no force push; no cross-node pooling.

## Kit / host / data / environment

- **Pre-U2 gate:** the accepted option-A code review C1–C3 must hold: Ada Linux/CPU tests (`tests/trackg`
  with the 19 Linux-only isolation tests included, plus full `test_port_autoresearch.py`) show no new failures
  vs `448f682`, and one **fresh clean isolated smoke** (not the 20 Nov co-tenant STOP) passes. Code review
  `TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha `261a03e9…`; fixed code report sha `370782ab…`.
- Suite autoresearch, node `autoresearch_fixedtokens`; kit branch `mac-trackg-iso-ar-cond7a-20261120`
  @ `73303380197477df971e865440d0ae11135fe1b3` (base `448f682`; isolation fix `5403392e` + option-A change).
  HEAD==tip and tracked-clean at launch; wrong/dirty kit = STOP.
  Pins: committed-file `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc` (20 entries) and
  deployed run-record pin (21 entries with data link; expected `069e987a…`), recorded separately; census uses
  the committed pin.
- Host Ada; Paper A three-check gate clear immediately before launch; **one smoke only, no retry of a unit
  failure**; an external co-tenant interruption is a STOP that needs fresh coordinator authorization and a
  card idle for the whole run. One **exclusively idle** GPU (no other
  user's compute app for the whole smoke; the 20 Nov attempt was stopped after a co-tenant appeared ~3 min
  after launch — that is an external STOP, not a unit result); ≥40 GiB free at launch (8 GiB cgroup is the run cap; 40 GiB is the headroom floor for the 1 GiB CPU
  logits buffer + parent/worker; prior watcher 8 GiB default was insufficient for the causal probe), UUID and cpuset
  recorded, 8 GiB delegated cgroup. Paper A has priority; never launch on a shared card.
- Data `/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens`, manifest
  `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51` (13 files, 963 M, outside repo);
  env `envs/torch312` (Python 3.12.16, torch 2.6.0+cu124; freeze `d2e70fe4…` at the accepted isolation
  checks; re-record). Licence/provenance: autoresearch MIT-declared README/climbmix MIT-claimed
  (`R1-TRACKG-LICENCES`), generic citation; data prepared by us.
- Verifier: use the COND7-aware verifier (`verify_ar_cond7a.py`), not the stale kit-update `verify_records.py`
  (the latter false-STOPs correct cond7a records because of the old §2/§7 text). Isolation: option A means **no CUDA IPC** in the result path (`run_fixed_budget.py`/`ar_worker.py` AST must
  contain no `cuda_share`/`cuda_open`/`_share_cuda_`/`bind_cuda` call sites); worker→parent logits via CPU
  `SharedBuffer`; `effective:true`, `waivers {}`, `exceptions []`, private `/dev/shm`
  (`shared_dev_shm:false`), log/result-channel/cgroup checks. A wrong/effective-false/waiver record is STOP.

## Run

- One isolated `port_smoke_gpu` on the accepted kit, inside
  `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c 'cd <kit> &&
  CG=$(cut -d: -f3 /proc/self/cgroup) && export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG && echo
  scope_cgroup=$AR_TEST_CGROUP_PARENT && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 && export
  PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH && export
  VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312 && export CUDA_VISIBLE_DEVICES="" && export
  AR_TRACKG_DATA_ROOT=… && taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node
  autoresearch_fixedtokens --gpu-uuid <UUID> --cpus <cpus> --memory-limit "external: systemd-run --user
  --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo> --provisional-timeout
  1800'`. One physical line; probe memory.max=8589934592/swap=0; record which python, scope.
- Expect 8 executed records + refused s001, `CHECKLIST_E_PASSED`, metric finite and B2 outcome **exactly equal** (the kit requires exact B2; `CAUSAL_ATOL` is the logits
  repeat/causality tolerance, not the B2 rule),
  no CUDA IPC error; record B1/B2 elapsed and `val_bpb`, node timeout = 3×B1 (provisional 1800 s), whole-smoke
  CPU/RAM aggregate and peak VRAM, **measured slowdown versus the 17 Nov un-isolated B1 67.901 s and 564 s
  smoke** (per-run and whole-smoke; the option-A CPU transport is ~1 GiB/batch and the report's estimate is
  97–161 s transfer per run, 2.4–3.4×; replace the estimate with measured values). A co-tenant arriving during the run is an external STOP: preserve, do not count as U2, do not retry on a
  shared card; a fresh smoke needs new authorization. Additional STOPs: CUDA-IPC error, non-finite metric,
  synthetic marker, gate/kit/data/env mismatch, disk < 50 GiB, timeout/OOM (proposal failure, no retry).
- Result fields: B1/B2, val_bpb, sealed if any, all edit outcomes, per-run hashes, `time -v`, GPU before/mid/
  after + co-tenant census, sampler/labels if used, env/data/pins/gate/disk/isolation, executed amended unit
  copy, result directory/sha, SHA256SUMS; one-node/no-evidence/no-noise statements; no push, no other host
  (TASL/HTCondor/deepthought), no secrets; record reviewed-unit sha and fresh worktree/runs-root.

## Review conditions

Fresh independent review before execution; check authority, kit tip/pins, option-A path, data/env,
isolation/cgroup, exclusive-idle requirement, command, slowdown measurement, record fields, STOPs,
one-node/no-evidence.

## Review conditions C1–C8 (for the independent reviewer)

C1 pre-U2 gate applied above; C2 one-smoke/no-retry/fresh-authorization/STOPs applied; C3 COND7-aware verifier
and stale-text note applied; C4 40 GiB floor/probe mismatch applied; C5 exact B2/mandatory sampler/result fields
applied; C6 slowdown method/licence/pins/worktree applied; C7 citations/scope applied; C8 execution rule: one
node, fresh smoke first, the 20 Nov co-tenant STOP is external, no retry of a unit failure.
