# Track G G.0 U2 raw cost — node `mlab_cifar10` (isolated kit) — unit, revision 3 (19 November 2026)

**Status: proposed unit revision 3; run only after a fresh independent review accepts it.** One node only.
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × census baseline B1; a timeout is a failed proposal, not an
infrastructure retry), the report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, and the accepted kit update report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (current sha `fe232e2b…`; reviewed `3c3ae74a…` plus C-K1…C-K4) with review `docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (not a PLAN
row of that name). ENGINEERING_ONLY census; no evidence/no noise floor/D21/D28; no T1 label; no
HTCondor/deepthought; no deletion; no force push; no cross-node pooling.

## Kit / host / data / licence

- Suite **MLAgentBench**, node **mlab_cifar10**; isolated kit branch
  `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9` (accepted kit update: isolation fix `5403392e` merged,
  all node copies and frozen pins updated). Before launch: `git rev-parse HEAD` equals this tip and
  `git status --porcelain --untracked-files=no` is empty; wrong/dirty kit = STOP. **Pins:** record the
  kit's **committed-file `frozen_pin_sha256`** (the value from accepted kit update §3/§10.2, the one the
  census commits) and the **deployed run-record pin** separately from the launch record; do not interchange
  them, and do not hardcode either in this unit (the kit update report's `pins/new_*.json` vs
  `deployed_*.json` define the convention). The census row uses the committed-file pin.
- Host Ada (`ucrtasl`); Paper A three-check gate (`paper_a_status.py --config
  r1/scripts/configs/paper_a_status_ada.json`) must be `clear_finished`, key false, no Paper A process,
  captured immediately before launch. One idle GPU only (UUID recorded), 8 GiB delegated cgroup, cpuset
  recorded; never disturb other users' cards/processes.
- Env `/home/dowling/r1_trackg_20261117/envs/torch312` (Python 3.12.16, torch 2.6.0+cu124; `uv pip freeze`
  sha recorded). `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data`; data manifest sha256
  **`43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3`**, outside repo, no synthetic marker. Record the setup command/manifest and the
  CPU-masked static-test result before the run.
- Licence/provenance: MLAgentBench tasks are used as task assets; CIFAR-10 generic research citation/disclosure per R1-TRACKG-LICENCES.
- Isolation requirement: every **executed** run record must have `isolation.effective: true`,
  `isolation.waivers == {}`, `isolation.exceptions == []`, `log_intact`, result channel, cgroup kill; a
  synthetic marker or non-effective record is a STOP. The refused frozen-diff `s001` record is
  `executed:false` and is not a failure; otherwise expect **8 executed records + the refused diff
  (`CHECKLIST_E_PASSED`)**.

## Run

- **Construct the cgroup inside the scope**, exactly as the accepted kit smoke did (run from the kit worktree root; `cd` is inside the scope):
  `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c 'cd <kit worktree root> && CG=$(cut -d: -f3 /proc/self/cgroup) && export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG && echo scope_cgroup=$AR_TEST_CGROUP_PARENT && export PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 && export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH && export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312 && export CUDA_VISIBLE_DEVICES="" && export AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data && taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node mlab_cifar10 --gpu-uuid <UUID> --cpus <cpus> --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside-repo>/u2_iso_mlab_cifar10_<UTC> --provisional-timeout 1800'`
  The `--memory-limit` value is one line (do not copy the markdown wrap); `CG`/`AR_TEST_CGROUP_PARENT` are computed inside the scope. After start, read and record `$AR_TEST_CGROUP_PARENT/memory.max` (expected `8589934592`) and `memory.swap.max` (expected `0`); a different value is a STOP. Record `which python`, the `scope_cgroup=` echo and the resolved invocation.
- GPU floor/co-tenancy: require a card with ≥ 8 GiB free and no other user's compute app; record
  `nvidia-smi` free/used/utilization and compute-app census before, once mid-run, and after; STOP if no
  qualifying card or an unrecorded card switch. Run a 1 s
  `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` sampler for the whole smoke.
  **Peak memory label:** these torch nodes have no per-run peak field. Report the sampler maximum as a
  **whole-smoke upper bound over the GPU(s) used, not a per-run peak and not attributed to the baseline
  process tree** unless a PID-tree mapping is available; record the sampler command, interval, output path
  and maximum in the result. A labelled whole-smoke upper bound is acceptable for U2; do not call it a
  per-run peak.
- Pre-run reference only: the kit update engineering smoke measured `12.859 s / val 0.5152`; this unit re-runs the
  checklist and records its own B1/B2. Provisional timeout 1800 s; node timeout = 3 × measured B1 and is
  recorded; no timeout/OOM retry.
- Result file must record baseline B1 `elapsed_seconds_info_only` and its metric name/value as the kit reports
  (`outcome.value` and, for test-scored nodes, the sealed test accuracy; these torch nodes have no `val_bpb`), B2 repeat and metric, all edit outcomes, labelled whole-smoke
  CPU/RAM `time -v`, GPU free/used/utilization + app census at three points, cgroup/memory cap and
  `memory.max`/`memory.swap.max`, sampler command/interval/output/max (whole-smoke upper bound label),
  host/boot/driver, env freeze sha, data manifest sha, kit tip + committed-file pin + deployed run-record
  pin, gate capture, disk before/after, isolation fields, `CHECKLIST_E_PASSED` and 8 executed + refused diff
  expectation, one-node/no-evidence/no-noise statements. Captures under
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_cifar10_<UTC>/` with SHA256SUMS; preserve, do not delete.
- STOPs: gate not clear; wrong/dirty kit or tip mismatch; data setup/manifest mismatch or env failure; no
  qualifying idle GPU or other users would be disturbed; cgroup/namespace condition missing
  (non-effective/waivers); synthetic marker; timeout/OOM; any executed record not `effective:true`; disk
  free < 50 GiB (cap 100 GiB) before/after; any cross-node or evidence/T1 use.

## Review conditions

A fresh independent reviewer must accept this revision before execution; the reviewer checks authority,
kit/pin identity and the committed-vs-deployed convention, data manifest, isolation/cgroup construction and
enforcement probe, command, GPU co-tenancy/floor, VRAM labelling, record fields, STOPs, one-node scope and
no-evidence constraints.
