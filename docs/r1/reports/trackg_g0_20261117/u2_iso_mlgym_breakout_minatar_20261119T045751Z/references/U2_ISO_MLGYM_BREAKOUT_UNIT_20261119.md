# Track G G.0 U2 raw cost — node `mlgym_breakout_minatar` (isolated kit, JAX) — unit (19 November 2026)

**Status: proposed unit; run only after a fresh independent review accepts it.** One node only. Authority:
`R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × census baseline B1; timeout = failed proposal, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, accepted kit
update report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha `fe232e2b…`;
reviewed `3c3ae74a…` plus C-K1…C-K4) and review. ENGINEERING_ONLY census; no evidence/noise/D21/D28; no T1;
no HTCondor/deepthought; no deletion; no force push; no cross-node pooling.

## Kit / host / env / data

- Suite MLGym, node `mlgym_breakout_minatar`; isolated kit branch `mac-trackg-iso-mlgym-20261117` @
  `f07875de79a5a57739227b13e0fd52d31646edaf` (accepted kit update, clean; HEAD==tip at launch).
  Pins: record the kit's committed-file `frozen_pin_sha256` (census value; accepted kit update §3/§10.2) and
  the deployed run-record pin separately; do not interchange them. Node spec:
  `third_party/mlgym/configs/trackg/nodes/mlgym_breakout_minatar.yaml` (`val_return`, test `test_return`,
  budget 2,000,000 env steps, no data setup: simulated gymnax Breakout-MinAtar).
- Host Ada; `git -C <kit> rev-parse HEAD` == tip and tracked-clean; committed pin `cec562e6…` (18-entry
  frozen file list) vs deployed run pin recorded separately; `setup_command` is empty / data none (simulated
  gymnax Breakout-MinAtar); Paper A gate command `r1/scripts/paper_a_status.py --config
  r1/scripts/configs/paper_a_status_ada.json` gives `clear_finished`, key false, no Paper A process, captured
  with UTC immediately before launch; one idle GPU (UUID recorded), 8 GiB
  delegated cgroup, cpuset recorded; no other users' processes touched.
- **JAX environment fix record:** `docs/r1/reports/trackg_g0_20261117/JAX_ENV_FIX_20261119.md`
  (sha `ad2d139a…`, committed with this unit) — cite it. **JAX environment** `/home/dowling/r1_trackg_20261117/envs/jax312` (Python 3.12.16; jax 0.4.35 with
  jax-cuda12 plugin; after the local fix removing the incompatible `nvidia-cuda-nvcc-cu12` package,
  `jax.devices()` returns the 8 Ada RTX 6000 devices; freeze sha recorded at launch, currently
  `d33c9612…`). Do not use `envs/torch312` for this node.
- Licence/provenance: MLGym task `rlBreakoutMinAtar` is CC BY-NC 4.0 (non-commercial; attribution and
  changes in the node's `LICENCES.md`), and the PPO/evaluation code adapted from gymnax-blines carries its
  Apache-2.0 notice (the node *uses* those parts, unlike the five torch nodes); include both in the result
  record and census provenance.
- Launch prechecks (inside the scope but before the smoke): `jax.devices()` must return the 8 Ada devices
  **without** `CUDA_VISIBLE_DEVICES=""`, `uv pip freeze --python envs/jax312/bin/python` sha equals the fix
  record's `d33c9612…`, and a `python -c "import tests.trackg.port_smoke_gpu"` entry dry-run succeeds (pytest
  is available in the env or record its absence as a STOP).
- Isolation requirement: every **executed** run record must have `isolation.effective: true`,
  `waivers == {}`, `exceptions == []`, log/result/cgroup checks; a synthetic marker or non-effective record
  is a STOP. `CHECKLIST_E_PASSED` + 8 executed records + refused frozen diff expected.

## Run

- Construct the cgroup **inside** the scope:
  `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c
  'cd <kit worktree root> && CG=$(cut -d: -f3 /proc/self/cgroup) && export
  AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG && echo scope_cgroup=$AR_TEST_CGROUP_PARENT && export
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 && export PATH=/home/dowling/r1_trackg_20261117/envs/jax312/bin:$PATH
  && export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/jax312 && export CUDA_VISIBLE_DEVICES=""
  && taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node mlgym_breakout_minatar --gpu-uuid <UUID>
  --cpus <cpus> --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"
  --runs-root <outside-repo>/u2_iso_mlgym_breakout_minatar_<UTC> --provisional-timeout 1800'`.
  **The launch command must be one physical line** (the wrapped block above is documentation; join the `&&`
  parts and keep `--memory-limit` one line). Read `$AR_TEST_CGROUP_PARENT/memory.max` (8G) and `memory.swap.max` (0)
  after start; a mismatch is a STOP. Record `which python` and `scope_cgroup`.
- GPU floor/co-tenancy: ≥ 8 GiB free, no other user's compute app, before/mid/after `nvidia-smi` and
  compute-app census, no unrecorded card switch. 1 s
  `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` whole-smoke sampler; record
  command/interval/output/max as a **whole-smoke upper bound**, not a per-run peak.
- Pre-run reference: the kit update's Breakout smoke did not run (JAX env was broken); there is no accepted
  pre-run baseline. Record B1/B2, node timeout = 3 × B1 (provisional 1800 s), no timeout/OOM retry.
- Result (full accepted standard): host/boot/driver, gate JSON+UTC, B1/B2 `elapsed_seconds_info_only`, `val_return` (outcome.value) and sealed `test_return`, all edit
  outcomes, labelled whole-smoke CPU/RAM, GPU census, cgroup probe, sampler fields, env freeze/data/none,
  kit tip + both pins, gate JSON+UTC, per-run records/logs + shas, `killed_with:null`,
  `determinism.not_forced`, sealed-value source (`AR_TEST test_return`), executed amended unit copy, disk, isolation fields, one-node/no-evidence/no-noise statements. Captures under
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_<UTC>/` with SHA256SUMS; preserve.
- STOPs: gate not clear; wrong/dirty kit; JAX import/device failure; no qualifying GPU; non-effective
  isolation; synthetic marker; timeout/OOM; any executed record not effective; disk < 50 GiB; any T1/evidence/
  cross-node use.

## Review conditions

A fresh independent reviewer must accept this unit before execution, checking authority, kit tip/pin
convention, JAX env fix/freeze and no torch-env use, isolation/cgroup construction, command, GPU co-tenancy,
VRAM labelling, record fields, STOPs, one-node/no-evidence scope.
