# Track G U4 census — isolated-kit raw-cost rows and readiness (20 November 2026; AR row added 21 November 2026)

**Status: ENGINEERING_ONLY census for U4, independent review requested.** Authority: `R1-TRACKG-G0-GO`,
`R1-HARNESS-ISOLATION`, `R1-TRACKG-PORT-DECISIONS`, `R1-TRACKG-G3-EARLY` (20 Nov: the six passed isolated
nodes are set now for G.1b/G.4; HousePrice joins now; autoresearch joins after a clean isolated smoke + U2; G.1b/G.4 no longer wait
for this report). No evidence/noise floor/D21/D28; no T1 label; no HTCondor/deepthought. All rows are
CPU/GPU isolated `port_smoke_gpu` measurements under effective isolation, one accepted unit and one smoke per
node (one executed smoke; no U2 retry), with 8 executed records + refused frozen diff and `CHECKLIST_E_PASSED`.
The 20 Nov Ada co-tenant STOP and 21 Nov retry-session STOPs are historical external-contention records
for the AR node, not U2 retries; the TASL-2 clean smoke supersedes them.

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
| autoresearch_fixedtokens | autoresearch | `7330338…` | 218.951 s | 1.293937 (val_bpb) | 218.443 s | 1.293937 (val_bpb) | n/a | 656.853 s | 12,436 MiB | `GPU-4d623e76…` (TASL-2 4090), cpus 0-7 | `147f0d35…` | `ab7186d2…` | `U2_ISO_AUTORESEARCH_RESULT_20261121.md`; captures dir `TASL2_AR_COND7A_RESULT_20261121_captures/` (7,055/7,055 OK, SHA256SUMS `32f5009a…`) | autoresearch README-MIT / climbmix MIT-claimed, no LICENSE file; data available; option A CPU transport |

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
| autoresearch_fixedtokens | 3,204,520 | `ca049086…` (TASL-2 path-dependent; Ada value `069e987a…`) | `TASL2_AR_COND7A_RESULT_20261121_captures/gate/gate_not_applicable.txt` (Paper A is on Ada; TASL-2 exclusivity controls substitute) | 388,531,040,256 -> 388,344,332,288 B |

The census uses the committed-file pin in the main table; the deployed pin above is the run-record value and is
not interchangeable. The seven torch rows' gate JSONs are `clear_finished`, key false, paper_a_processes [], captured with UTC;
the AR row is on TASL-2, has no Paper A, and records `gate_not_applicable.txt` plus exclusivity controls. Disk
before/after and per-run hashes are in the record captures.

All eight rows: one unit, one executed smoke, no U2 retry; 8 executed + refused `s001`; every executed record
`isolation.effective:true`, `waivers {}`, `exceptions []`, log/result-channel/cgroup.kill checks; inside-scope
`memory.max=8589934592`, `memory.swap.max=0`; Paper-A three-check gate clear (AR row on TASL-2 has no Paper A; exclusivity controls and no other compute app recorded instead); idle GPU (HousePrice: selected
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
- **autoresearch (1 node):** **passed** on TASL-2 under author-signed `R1-TRACKG-AR-U2-TASL2` with option A:
  one clean isolated smoke, B1 218.951 s/val_bpb 1.293937, B2 218.443 s exact, isolation effective/no
  waivers/no CUDA IPC, slowdown 3.225× cross-host composite vs the 17 Nov Ada un-isolated L40S U2 67.901 s (bpb/VRAM not normalised), transfer
  0.2345 s/request; result review ACCEPTED **conditional on C1–C5**; C1–C4 text conditions are partially applied (executed sibling unit copy `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` sha `b83d9159…`; reviewed `3bb015a1…` not preserved; parent peak 6,560.3 MB recorded in the U2 result). The 20 Nov Ada co-tenant
  OOM and the 21 Nov retry STOP remain preserved as historical external-contention evidence, superseded by
  the TASL-2 clean smoke. T1 labels remain on H200.
- No node was dropped; every attempted row that failed pre-launch is disclosed in its record (attempt-1
  pre-launch refusals: HousePrice CPU-idle STOP, Breakout gate STOP, etc.).

AR row measurement notes: whole smoke wall 1,791.0 s (3.176× the 17 Nov 564 s smoke), worker peak
VRAM 1,980.1 MB (max run 3,720.4 MB), parent peak 6,560.3 MB, cgroup peak 5.17 GiB with OOM 0/swap 0,
sampler upper bound 12,436 MiB (not per-run); transferred via CPU memfd (no CUDA IPC); committed pin
`147f0d35…` (20 entries), deployed TASL-2 pin `ca049086…` (21, path-dependent). The clean smoke is the U2
measurement; no second U2 run; author row `R1-TRACKG-AR-U2-TASL2` is signed and reaches main after the
sweep-2 launch. U2 result `U2_ISO_AUTORESEARCH_RESULT_20261121.md` (review conditional C1–C5; executed amended
unit sibling copy `U2_ISO_AUTORESEARCH_RESULT_20261121_unit.md` sha `b83d9159…`; reviewed `3bb015a1…` not
preserved — recorded residual; TASL-2 adaptations: host TASL-2, env `ar-cond7a`, data root
`/home/dowling/r1_trackp/data`, 20,000 MiB free floor, no Paper A gate).

## Kitchen / environment

- Kit branches: `mac-trackg-iso-mlab-20261117` @ `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`;
  `mac-trackg-iso-mlgym-20261117` @ `f07875de79a5a57739227b13e0fd52d31646edaf`, both containing the accepted
  isolation core fix `5403392e` and updated node copies/frozen pins. Ada isolation host checks: condition 6 PASS (fix report `HARNESS_ISOLATION_FIX_20261119.md`, sha `0ff9a7f2…`; fix review `HARNESS_ISOLATION_FIX_REVIEW_20261119.md` sha `c8e468c7…`, ACCEPTED) and condition 7 GPU CUDA-IPC blocked and disclosed (the earlier
  host-check `HARNESS_ISOLATION_HOST_CHECK_20261119.md` records the pre-fix STOP; the fix report supersedes it).
- Environment: `envs/torch312` (Python 3.12.16, torch 2.6.0+cu124; the five torch nodes and HousePrice);
  `envs/jax312` (jax 0.4.35 CUDA-12 after removing `nvidia-cuda-nvcc-cu12`; Breakout). Exact freezes and pins
  are in each node's result/pins/captures.

## Blocked / not passed

- **All eight nodes have now passed isolated U2.** `autoresearch_fixedtokens` passed on **TASL-2** under the
  author-signed `R1-TRACKG-AR-U2-TASL2` after TASL-2 host checks PASS/accepted and the option-A clean smoke
  (`U2_ISO_AUTORESEARCH_RESULT_20261121.md`, accepted; one host difference TASL-2/4090 vs the earlier Ada
  attempt; B1 218.951 s vs Ada 67.901 s = **3.225× cross-host option-A slowdown**, 0.2345 s/request wall-clock surrogate;
  B2 exact; effective:true/waivers {}/exceptions []; no CUDA IPC; slowdown measured). The 20 Nov Ada failure and
  retry STOP remain preserved as external co-tenancy evidence, superseded by the TASL-2 clean smoke. No node
  remains blocked.
- No other node is blocked. HousePrice is now passed; Breakout is passed.

## Readiness

Per `R1-TRACKG-G3-EARLY`, the six earlier nodes, HousePrice and (after the TASL-2 clean smoke/U2) autoresearch
are all set; the author row `R1-TRACKG-AR-U2-TASL2` is signed but not yet in committed PLAN at this review time;
T1 labels remain on H200 per `R1-T1-HOST-H200`. All eight rows are complete in the census sense; this census does not block
G.1b/G.4 and is not evidence.


## Authority and acceptance citations

The 21 Nov addendum `TRACKG_U4_CENSUS_ADDENDUM_20261121.md` is superseded by this revision's AR row; it remains
as the historical pre-clean-smoke record. CUDA IPC is not tested; the AR row uses option A's CPU memfd path
only, and no `cuda_share`/`cuda_open` node is covered by this census.

Plan rows: `R1-TRACKG-G0-GO` (main `de3de54f` PLAN:1258), `R1-TRACKG-LICENCES` (:1269),
`R1-TRACKG-PORT-DECISIONS` (:1289), `R1-HARNESS-ISOLATION` (:1290), `R1-TRACKG-G3-EARLY` (:1330).
Acceptances: kit update report `TRACKG_ISO_KIT_UPDATE_20261119.md` + review; two result reviews cover the six
earlier torch nodes (`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md`, `TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`),
the HousePrice result review is `TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md`, and the AR U2 result review is
`U2_ISO_AUTORESEARCH_RESULT_REVIEW_20261121.md` sha `9de24ec5…`; TASL-2 host-check report
`TASL2_ISOLATION_HOST_CHECK_20261121.md` sha `83636c03…` (successor of pre-fix `0a1fa3a4…`) / review
`TASL2_ISOLATION_HOST_CHECK_REVIEW_20261121.md` sha `bfe9b231…`; TASL-7 host-check report
`TASL7_ISOLATION_HOST_CHECK_20261121.md` sha `2b703226…` / review `TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md`
sha `18e261cd…`; AR U2 result final sha `8f872f2d…` 76 lines/5,845 B (reviewed `ca3bcadd…` 57/3,893; intermediates `8430854c…` 67/5,181 and `c03f0cbd…` 67/5,204 (+23 B parent-peak); reviewed→final = +19 lines/+1,952 B, c03f→final = +9 lines/+641 B; executed unit sibling `b83d9159…` 74/6,374 B; open U2-review C3/C4 residuals recorded in the U2 result), smoke `TASL2_AR_COND7A_RESULT_20261121.md` sha `8814eecc…`,
captures SHA256SUMS `32f5009a…` (7,055/7,055 OK). Authority rows: `R1-TRACKG-AR-COND7` at origin/main
`df58bcd5` PLAN:1317, `R1-T1-HOST-H200` PLAN:1329, `R1-TRACKG-G3-EARLY` PLAN:1330.


Revision/acceptance traceability (21 Nov): this revision is the census after the U4 AR-row acceptance
chain. R3 object `79ad29ca…` (123 lines/12,634 B) and R4 object `2dbf2c16…` (136/13,984 B) → final revision; the
exact final sha/lines/bytes and the R3/R4→final deltas are computed after this write and recorded in the sidecar; the R3 and R4 object bytes are not preserved (only their quoted sizes).
R5-carried conditions (seven-node R5 C4–C10) dispositions: duplicate fix-review reference removed (closed);
licence/availability per U1 §7 partially applied (licence cell added; per-node U1 §7 wording not complete);
citations/shas largely closed (authority rows and review/report shas added; minor gaps remain); verbatim imdb
sentence not applied (partial); CPU/RAM wording partially corrected; binding/preservation via this sidecar
(closed for sha binding; evidence bytes for some superseded objects not preserved); commit of AR evidence and
SHA256SUMS caveat pending this commit. R5 had 2 MAJOR (not 3); this sidecar does not claim all conditions are
closed. The exact
current census sha256 is recorded in `TRACKG_U4_CENSUS_ACCEPTANCE_20261121.md` (sidecar written after this file;
binding record). Executed unit sibling `b83d9159…` is byte-identical
to the committed Ada-targeted unit (not in the 7,055-entry captures); reviewed unit `3bb015a1…` not preserved.
