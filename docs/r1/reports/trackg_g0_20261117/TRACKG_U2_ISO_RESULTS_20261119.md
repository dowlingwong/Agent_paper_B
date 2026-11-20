# Track G G.0 U2 raw cost on the isolated kits — five-node result summary (19 November 2026)

**ENGINEERING_ONLY census; no evidence/noise floor/D21/D28; no T1 label; one node per accepted unit.**
Authority: `R1-TRACKG-G0-GO`, `R1-HARNESS-ISOLATION`, `R1-TRACKG-PORT-DECISIONS`, port report §7.
Units rev 3 accepted by R3 review (`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md`); results
independently reviewed and ACCEPTED per node (`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md`);
MINOR record corrections applied (`U2_ISO_RECORD_CORRECTIONS_20261119.md`).

| Node | B1 elapsed | B1 `outcome.value` | B2 elapsed | B2 value | sealed test | whole-smoke VRAM upper bound | GPU (card) | committed-file pin | record |
|---|---|---|---|---|---|---|---|---|---|
| mlab_cifar10 | 12.297 s | 0.5152 (val_accuracy) | 11.846 s | 0.5152 | 0.5015 | 836 MiB | `GPU-aa340032…` (1) | `1f047ad7…` | `u2_iso_mlab_cifar10_20261119T033747Z/` |
| mlab_imdb | 64.142 s | 0.9048 | 64.133 s | 0.9048 | 0.89924 | 11,292 MiB | `GPU-f439cca8…` (2) | `4b1019a6…` | `u2_iso_mlab_imdb_20261119T034107Z/` |
| mlab_ogbn_arxiv | 5.651 s | 0.275982 | 5.665 s | 0.275982 | 0.238442 | 4,544 MiB | `GPU-3b36edea…` (6) | `bd71fdf4…` | `u2_iso_mlab_ogbn_arxiv_20261119T035109Z/` |
| mlgym_cifar10 | 31.731 s | 0.491 (val_accuracy) | 31.244 s | 0.491 | 0.4926 | 982 MiB | `GPU-3719bd35…` (7) | `2d7e533b…` | `u2_iso_mlgym_cifar10_20261119T035326Z/` |
| mlgym_fmnist | 34.376 s | 0.861667 (val_accuracy) | 28.868 s | 0.861667 | 0.8515 | 912 MiB | `GPU-f439cca8…` (2) | `eb60107e…` | `u2_iso_mlgym_fmnist_20261119T035842Z/` |
| mlgym_breakout_minatar | 61.248 s | 22.486719 (val_return) | 61.781 s | 22.486719 | 22.885938 | 634 MiB | `GPU-3b36edea…` (6) | `cec562e6…` | `u2_iso_mlgym_breakout_minatar_20261119T045751Z/` |
| mlgym_houseprice | 5.059 s | 23344.767385 (val_rmse) | 4.876 s | 23344.767385 | 30295.671017 (test_rmse) | n/a (CPU) | 8 cpus | `88d359f2…` | `u2_iso_mlgym_houseprice_20261120T215244Z/` |

All seven: one smoke per node, no retry; 8 executed records + refused frozen diff (`s001 executed:false`);
`CHECKLIST_E_PASSED`; every executed record `isolation.effective:true`, `waivers {}`, `exceptions []`,
`log_intact`, result channel, cgroup.kill; inside-scope `memory.max=8589934592`, `memory.swap.max=0`;
`--provisional-timeout 1800`; node timeout = 3 × B1 (36.891 / 192.426 / 16.953 / 95.193 / 103.128 s);
no timeout/OOM; Paper A gate clear; idle GPU, no other app, before/mid/after census; whole-smoke CPU/RAM
aggregates labelled; env freeze/data manifest/kit tips/both pins/gate/disk recorded. The whole-smoke VRAM
number is a **whole-smoke upper bound over the used GPU (sampler per-sample sum, includes co-tenants by
construction), not a per-run peak and not a baseline-tree attribution**.

Breakout is the JAX node: `envs/jax312` was fixed by removing the incompatible `nvidia-cuda-nvcc-cu12`
package (JAX fix record `JAX_ENV_FIX_20261119.md`); the test-only pytest add raised the launch freeze from
65 lines (`d33c9612…` sorted) to 68 lines (`80a455c6…` sorted) with JAX versions/devices unchanged. The
result review (`TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md`) accepted it with MINOR record corrections
(`U2_ISO_BREAKOUT_RECORD_CORRECTIONS_20261119.md`).

**HousePrice (20 Nov):** author Kaggle train.csv `1e18addf…929d41` / md5 `80ccab65…b5577`, `--from-file`; result accepted (`TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md`).

**Blocked nodes (not U2):** `autoresearch_fixedtokens` — option A code is implemented/reviewed
(`mac-trackg-iso-ar-cond7a-20261120`), but its one isolated Ada smoke was STOPPED by an external co-tenant
CUDA OOM (zihaozhao, 9 pids, ~42.6 GiB started ~3 min after idle launch); no CUDA IPC error, isolation
effective, slowdown not measured, no retry. A fresh clean isolated smoke needs an idle card for the whole
run; then the autoresearch U2. No other U2 blocker remains.

Captures: the five result directories above (each `U2_ISO_<NODE>_RESULT_20261119.md`, captures, executed
unit copy, static logs, runner/verifier sources, SHA256SUMS). No deletion, no force push, no
HTCondor/deepthought, no other users' processes touched.
