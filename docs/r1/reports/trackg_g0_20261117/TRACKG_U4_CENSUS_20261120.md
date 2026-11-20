# Track G U4 census — isolated-kit raw-cost rows and readiness (20 November 2026)

**Status: ENGINEERING_ONLY census for U4, independent review requested.** Authority: `R1-TRACKG-G0-GO`,
`R1-HARNESS-ISOLATION`, `R1-TRACKG-PORT-DECISIONS`, `R1-TRACKG-G3-EARLY` (20 Nov: the six passed isolated
nodes are set now for G.1b/G.4; HousePrice joins now; autoresearch joins after a clean isolated smoke + U2; G.1b/G.4 no longer wait
for this report). No evidence/noise floor/D21/D28; no T1 label; no HTCondor/deepthought. All rows are
CPU/GPU isolated `port_smoke_gpu` measurements under effective isolation, one accepted unit and one smoke per
node (no retry), with 8 executed records + refused frozen diff and `CHECKLIST_E_PASSED`.

## Passed rows

| node | suite | kit tip | B1 elapsed | B1 metric | B2 elapsed | B2 metric | sealed test | timeout = 3×B1 | whole-smoke upper bound | GPU/cpus | committed-file pin | data manifest sha256 | record | licence/availability |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | MLAgentBench | `fb6e7d73…` | 12.297 s | 0.5152 (val_accuracy) | 11.846 s | 0.5152 (val_accuracy) | 0.5015 (test_accuracy) | 36.891 s | 836 MiB | `GPU-aa340032…` (1), cpus 0-7 | `1f047ad7…` | `43fdf860…` | `u2_iso_mlab_cifar10_20261119T033747Z/` | CIFAR-10 generic citation; data present |
| mlab_imdb | MLAgentBench | `fb6e7d73…` | 64.142 s | 0.9048 (val_accuracy) | 64.133 s | 0.9048 (val_accuracy) | 0.89924 (test_accuracy) | 192.426 s | 11,292 MiB | `GPU-f439cca8…` (2), cpus 0-7 | `4b1019a6…` | `a87254e1…` | `u2_iso_mlab_imdb_20261119T034107Z/` | baseline written by us (DistilBERT); IMDb citation |
| mlab_ogbn_arxiv | MLAgentBench | `fb6e7d73…` | 5.651 s | 0.275982 (val_accuracy) | 5.665 s | 0.275982 (val_accuracy) | 0.238442 (test_accuracy) | 16.953 s | 4,544 MiB | `GPU-3b36edea…` (6), cpus 0-7 | `bd71fdf4…` | `91312162…` | `u2_iso_mlab_ogbn_arxiv_20261119T035109Z/` | OGB/arXiv generic citation; data present |
| mlgym_cifar10 | MLGym | `f07875de…` | 31.731 s | 0.491 (val_accuracy) | 31.244 s | 0.491 (val_accuracy) | 0.4926 (test_accuracy) | 95.193 s | 982 MiB | `GPU-3719bd35…` (7), cpus 8-15 | `2d7e533b…` | `c0ef1168…` | `u2_iso_mlgym_cifar10_20261119T035326Z/` | MLGym CC BY-NC 4.0; CIFAR citation |
| mlgym_fmnist | MLGym | `f07875de…` | 34.376 s | 0.861667 (val_accuracy) | 28.868 s | 0.861667 (val_accuracy) | 0.8515 (test_accuracy) | 103.128 s | 912 MiB | `GPU-f439cca8…` (2), cpus 8-15 | `eb60107e…` | `8d28287b…` | `u2_iso_mlgym_fmnist_20261119T035842Z/` | MLGym CC BY-NC 4.0; Fashion-MNIST citation |
| mlgym_breakout_minatar | MLGym | `f07875de…` | 61.248 s | 22.486719 (val_return) | 61.781 s | 22.486719 (val_return) | 22.885938 (test_return) | 183.744 s | 634 MiB | `GPU-3b36edea…` (6), cpus 8-15 | `cec562e6…` | none (simulated) | `u2_iso_mlgym_breakout_minatar_20261119T045751Z/` | MLGym CC BY-NC 4.0; gymnax-blines Apache-2.0 used |
| mlgym_houseprice | MLGym | `f07875de…` | 5.059 s | 23344.767385 (val_rmse) | 4.876 s | 23344.767385 (val_rmse) | 30295.671017 (test_rmse) | 15.177 s | n/a (CPU; max RSS 599,392 kB) | cpus 79,78,77,76,59,42,34,28 | `88d359f2…` | `73ee5597…` | `u2_iso_mlgym_houseprice_20261120T215244Z/` | MLGym CC BY-NC 4.0; author Kaggle train.csv |

Run-level facts (all from the per-node record/captures; base path `docs/r1/reports/trackg_g0_20261117/`):

| node | whole-smoke max RSS (kB) | deployed run-record pin | gate capture | disk before/after |
|---|---|---|---|---|
| mlab_cifar10 | 1,402,612 | `a459b3d8…` | `u2_iso_mlab_cifar10_20261119T033747Z/gate/gate_20261119T033747Z.json` | 74,632,835,072 -> 74,630,283,264 B |
| mlab_imdb | 1,659,008 | `c169a6b8…` | `u2_iso_mlab_imdb_20261119T034107Z/gate/gate_20261119T034107Z.json` | 74,629,115,904 -> 74,609,201,152 B |
| mlab_ogbn_arxiv | 1,256,776 | `5ff5824a…` | `u2_iso_mlab_ogbn_arxiv_20261119T035109Z/gate/gate_20261119T035109Z.json` | 74,610,388,992 -> 74,605,633,536 B |
| mlgym_cifar10 | 1,493,864 | `817c9034…` | `u2_iso_mlgym_cifar10_20261119T035326Z/gate/gate_20261119T035326Z.json` | 74,604,687,360 -> 74,597,408,768 B |
| mlgym_fmnist | 1,213,024 | `ef804338…` | `u2_iso_mlgym_fmnist_20261119T035842Z/gate/gate_20261119T035842Z.json` | 74,596,868,096 -> 74,548,490,240 B |
| mlgym_breakout_minatar | 1,262,488 | `cec562e6…` (equal to committed) | `u2_iso_mlgym_breakout_minatar_20261119T045751Z/gate/gate_20261119T045751Z.json` | 75,439,427,584 -> 75,401,625,600 B |
| mlgym_houseprice | 599,392 | `4cbbc5d6…` | `u2_iso_mlgym_houseprice_20261120T215244Z/gate/gate_20261120T215244Z.json` | 70,644,187,136 -> 70,795,374,592 B |

The census uses the committed-file pin in the main table; the deployed pin above is the run-record value and is
not interchangeable. Each row's gate JSON is `clear_finished`, key false, paper_a_processes [], captured with
UTC; disk before/after and per-run hashes are in the record captures.

All seven rows: one unit, one executed smoke, no retry; 8 executed + refused `s001`; every executed record
`isolation.effective:true`, `waivers {}`, `exceptions []`, log/result-channel/cgroup.kill checks; inside-scope
`memory.max=8589934592`, `memory.swap.max=0`; Paper-A three-check gate clear; idle GPU (HousePrice: selected
CPU cpuset) with before/mid/after co-tenancy census; whole-smoke CPU/RAM aggregates labelled; whole-smoke VRAM
numbers are upper bounds over the used GPU (sampler per-sample sum, includes co-tenants by construction), not
per-run peaks. Data outside repo; no synthetic marker; ENGINEERING_ONLY. Licences/provenance recorded per
node (MLAgentBench tasks/IMDb/OGB arXiv generic citation; MLGym CC BY-NC 4.0 with notice and gymnax-blines
Apache-2.0 parts used only by Breakout; HousePrice author Kaggle `train.csv` sha256
`1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`, md5
`80ccab65fb115cbad143dbbd2bcd5577`, `--from-file`, no MLGym copy).

## Census funnel and per-suite appendix (R1-TRACKG-PORT-DECISIONS (3); R1-TRACKG-G0-GO)

- **MLAgentBench (3 nodes):** mlab_cifar10, mlab_imdb, mlab_ogbn_arxiv — all passed isolated U2. The
  `mlab_imdb` baseline was **written by us** (the kit fine-tunes DistilBERT-base-uncased; MLAgentBench ships only
  a skeleton and no upstream baseline), frozen, reviewed and disclosed as ours; the census/paper appendix must
  carry this disclosure. The other two use generic data/task assets.
- **MLGym (4 nodes):** mlgym_cifar10, mlgym_fmnist, mlgym_breakout_minatar, mlgym_houseprice — all passed.
  MLGym subtree CC BY-NC 4.0 with notice; Breakout also uses gymnax-blines Apache-2.0 parts (notice required);
  HousePrice uses only the author's Kaggle `train.csv` (`--from-file`, sha256/md5 above), not MLGym's copy.
- **autoresearch (1 node):** not in this census; condition-7 option-A code unit accepted, but the one isolated
  Ada smoke was attempted and STOPPED (external co-tenant CUDA OOM; slowdown not measured; no retry). It
  joins after a fresh clean isolated smoke + U2 review.
- No node was dropped; every attempted row that failed pre-launch is disclosed in its record (attempt-1
  pre-launch refusals: HousePrice CPU-idle STOP, Breakout gate STOP, etc.).

## Kitchen / environment

- Kit branches: `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`;
  `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf`, both containing the accepted
  isolation core fix `5403392e` and updated node copies/frozen pins. Ada isolation host checks: condition 6 PASS (fix report `HARNESS_ISOLATION_FIX_20261119.md`, sha `0ff9a7f2…`; fix review `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha `c8e468c7…`, ACCEPTED);
  `HARNESS_ISOLATION_FIX_REVIEW_20261119.md`) and condition 7 GPU CUDA-IPC blocked and disclosed (the earlier
  host-check `HARNESS_ISOLATION_HOST_CHECK_20261119.md` records the pre-fix STOP; the fix report supersedes it).
- Environment: `envs/torch312` (Python 3.12.16, torch 2.6.0+cu124; the five torch nodes and HousePrice);
  `envs/jax312` (jax 0.4.35 CUDA-12 after removing `nvidia-cuda-nvcc-cu12`; Breakout). Exact freezes and pins
  are in each node's result/pins/captures.

## Blocked / not passed

- **autoresearch_fixedtokens** — isolation condition 7 (CUDA IPC across user/PID namespace) failed on
  Ada pre-fix. Option A is authorized (`R1-TRACKG-AR-COND7`): harness/kit branch
  `mac-trackg-iso-ar-cond7a-20261120` (pushed; code reviewed at `13786d1f…`, review
  `TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` sha `261a03e9…` ACCEPTED with 1 report-only MAJOR + 6 MINOR;
  current report tip `7330338…`, report sha `370782ab…`) removes CUDA IPC from the result path and adds
  `torch.cuda.init()`. **The one isolated Ada GPU smoke was attempted on 20 Nov:** launched 22:35:48Z on
  card 5 (`GPU-5357dc5f…`, verified idle), but a co-tenant (zihaozhao, 9 processes, 42,570 MiB (≈41.6 GiB)) started
  ~3 min later and the baseline died with `CUDA out of memory`; the smoke was STOPPED at 22:54:22Z
  (`DONE_STOP`, rc 137), only the baseline record + refused s001 exist, no `CHECKLIST_E_PASSED`, and the
  **transfer slowdown was not measured**. Result record `ar_cond7a_smoke_20261120T223548Z/`
  (`U2_ISO_AR_COND7A_RESULT_20261120.md` sha `bcb74efc…`, SHA256SUMS `231d388e…`). This is an external
  co-tenancy failure, not a code failure: no CUDA IPC error, isolation `effective:true/waivers {}/exceptions
  []`, private `/dev/shm`, and the training phase completed (500 steps, peak VRAM 1,980.1 MB); the frozen
  pin was `147f0d35…` (committed) / `069e987a…` (deployed). One smoke was consumed; **no retry was made and a new smoke needs fresh authorization**, and a fresh isolated smoke needs a guaranteed-idle card for the whole run. The isolated
  autoresearch U2 is **not run** (the 17 Nov un-isolated U2 passed B1 67.901 s); the row joins G.1b/G.4 only
  after a clean smoke + U2 review. 
- No other node is blocked. HousePrice is now passed; Breakout is passed.

## Readiness

Per `R1-TRACKG-G3-EARLY`, the six earlier passed nodes are set for G.1b/G.4; HousePrice joins now; autoresearch
joins when its option-A smoke + U2 pass. This census does not block G.1b/G.4 and is not evidence; autoresearch remains blocked as above.


## Authority and acceptance citations

Plan rows: `R1-TRACKG-G0-GO` (main `de3de54f` PLAN:1258), `R1-TRACKG-LICENCES` (:1269),
`R1-TRACKG-PORT-DECISIONS` (:1289), `R1-HARNESS-ISOLATION` (:1290), `R1-TRACKG-G3-EARLY` (:1330).
Acceptances: kit update report `TRACKG_ISO_KIT_UPDATE_20261119.md` + review; six isolated U2 result reviews
(`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md`, `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`); HousePrice
unit R2 review `TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md` and result review
`TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md`; isolation fix review. Record base path
`docs/r1/reports/trackg_g0_20261117/`.
