# Track G G.0 U2 raw cost — node `mlgym_houseprice` (isolated kit, CPU) — unit (20 November 2026)

**Status: proposed unit; run only after a fresh independent review accepts it.** One node only. Authority:
`R1-TRACKG-G0-GO`, `R1-HARNESS-ISOLATION`, `R1-TRACKG-PORT-DECISIONS` (2) (House Prices must use the user's
Kaggle `train.csv` via `--from-file`; its sha256 recorded; no MLGym copy), port report
`docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, accepted kit update report
`docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha `fe232e2b…`; reviewed
`3c3ae74a…` plus C-K1…C-K4) and review. ENGINEERING_ONLY census; no evidence/noise/D21/D28; no T1;
no HTCondor/deepthought; no deletion; no force push; no cross-node pooling.

## Input (author-supplied) — verified

- Path `/home/dowling/house-prices-advanced-regression-techniques/train.csv` (the author placed it there on
  20 Nov — this is a deliberate path move from the earlier `~/r1_inputs/house-prices/train.csv`; **no copy**;
  record the actual path beside the hashes).
- Full sha256 **`1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`** (prefix `1e18addf`,
  suffix `929d41`); md5 **`80ccab65fb115cbad143dbbd2bcd5577`**; size 450 K, 1,461 lines. Verify before setup and
  record both hashes (sha256 + md5), the author's path, and the manifest's `from_file_name` (the manifest
  records the file name, not the path; do not claim the path appears in the manifest); a mismatch is a STOP. The hash happens to equal MLGym's copy
  (`same_as_mlgym_copy` informational) — record it, but the setup must still use the author's file. Only
  `train.csv` is used; no other Kaggle file.

## Kit / host / env

- MLGym node `mlgym_houseprice`; isolated kit branch `mac-trackg-iso-mlgym-20261117` @
  `f07875de79a5a57739227b13e0fd52d31646edaf` (HEAD==tip and tracked-clean; the **committed-file
  `frozen_pin_sha256` for mlgym_houseprice is the kit update §3/§9 / `pins/new_mlgym.json` value, not another
  node's pin** — read the full 64-hex at launch and record it; the deployed run-record pin is recorded
  separately; the census uses the committed-file pin. Do not hardcode either without re-reading).
- Setup (guarded, logged): run from the node dir with the env python first on PATH; `test -n
  "$AR_TRACKG_DATA_ROOT" && test -n "$AR_HOUSEPRICE_TRAIN_CSV" && python3 prepare_data.py --out ...
  --from-file ...`; record the exact command/rc/log and the resulting `data_manifest.json` sha256; a setup
  failure is a STOP; if a partial data dir exists, move it aside (no deletion). Syntax: `setup_command` with `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` and
  `AR_HOUSEPRICE_TRAIN_CSV=/home/dowling/house-prices-advanced-regression-techniques/train.csv`
  (`prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice" --from-file "$AR_HOUSEPRICE_TRAIN_CSV"`);
  record the created `data_manifest.json` sha256 and confirm `synthetic` is false and the source path/hash
  appear. Env `envs/torch312` (Python 3.12.16, sklearn/pandas; CPU node, no GPU). Data outside repo.
- Licence/provenance (cite `R1-TRACKG-LICENCES`): MLGym task `regressionKaggleHousePrice` CC BY-NC 4.0 (non-commercial, attribution and
  changes in `LICENCES.md`); the Kaggle House Prices table is used under the user's Kaggle terms; only
  `train.csv`; no MLGym copy. Record both.
- Paper A gate clear (`clear_finished`, key false, no Paper A process) immediately before launch; capture
  the gate JSON + UTC. CPU co-tenancy: record load, CPU jobs, users and `/proc` CPU count before/mid/after
  and do not disturb other users; STOP if the host is too loaded or a foreign job would be affected. 8 GiB
  delegated cgroup, cpuset. Launch check: kit HEAD==tip, tracked-clean, `which python`, env import check.

## Run (CPU)

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c
  'cd <kit worktree root> && CG=$(cut -d: -f3 /proc/self/cgroup) && export
  AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG && echo scope_cgroup=$AR_TEST_CGROUP_PARENT && export
  PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 && export PATH=/home/dowling/r1_trackg_20261117/envs/torch312/bin:$PATH
  && export VIRTUAL_ENV=/home/dowling/r1_trackg_20261117/envs/torch312 && export CUDA_VISIBLE_DEVICES=""
  && taskset -c <cpus> python -m tests.trackg.port_smoke_gpu --node mlgym_houseprice --cpus <cpus>
  --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"
  --runs-root <outside-repo>/u2_iso_mlgym_houseprice_<UTC> --provisional-timeout 1800'`.
  **The launch command must be one physical line** (the block is documentation; join all `&&` parts and keep
  `--memory-limit` one line; a verbatim multi-line copy does not parse). No `--gpu-uuid` (CPU node).
  `--memory-limit` one line; read `$AR_TEST_CGROUP_PARENT/memory.max`
  (8589934592) and `memory.swap.max` (0); mismatch STOP. Record `which python`, `scope_cgroup`.
- No GPU/VRAM fields required; record CPU `time -v`, CPU before/mid/after snapshot, memory cap, disk.
- Pre-run reference: none accepted (this is the first HousePrice isolated run); run the CPU-masked static
  tests (or record why not) before the smoke. B1/B2, metric
  `val_rmse` (outcome.value) and sealed `test_rmse`, budget one fit (`steps 1`); node timeout = 3 × B1;
  provisional 1800 s; no timeout/OOM retry.
- Result (full accepted standard): B1/B2 elapsed+`val_rmse`+sealed `test_rmse` (name the sealed source
  `AR_TEST test_rmse`), all edit outcomes, per-run record/log/result-channel shas, `killed_with:null`,
  `determinism.not_forced`, node-spec/representative-edit shas, `CHECKLIST_E_PASSED` + 8 executed + refused s001,
  isolation `effective:true`/waivers {}/exceptions [], cgroup probe, CPU/load census, gate JSON+UTC,
  host/kernel, env freeze, data manifest + source csv sha256/md5, kit tip + both pins, licence, disk,
  executed amended unit copy, result directory path + own/sha, captures + SHA256SUMS. STOPs: csv missing/hash mismatch; data setup failure;
  wrong/dirty kit; gate not clear; non-effective isolation; synthetic marker; timeout/OOM; disk <50 GiB;
  any T1/evidence/cross-node use, no push/deletion, no other host (TASL/HTCondor/deepthought), no secrets.

## Review conditions

A fresh independent reviewer must accept this unit before execution, checking authority, author csv
sha256/md5 and `--from-file` path, data setup, kit tip/pins, isolation/cgroup, CPU command, record fields,
STOPs, one-node/no-evidence scope.
