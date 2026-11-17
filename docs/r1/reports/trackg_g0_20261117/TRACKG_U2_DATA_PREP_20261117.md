# Track G G.0 U2 — deployment/data preparation status (17 November 2026)

**ENGINEERING_ONLY; no node run yet except autoresearch_fixedtokens (PASSED, separate record).** Authority
`R1-TRACKG-G0-GO`, `R1-TRACKG-PORT-OWNER`, `R1-TRACKG-LICENCES`, `R1-TRACKG-PORT-DECISIONS` (main
`50176481`). AI-assisted.

## Kits / env

- Harness worktrees: `harness_ar` @ `08d06507…`, `harness_mlab` @ `8596a0ec…`, `harness_mlgym` @
  `334c89ce…` (base `717ad835`, clean); paper `main 50176481`.
- Python 3.12.16 `envs/torch312`: torch 2.6.0+cu124, transformers 4.49.0, numpy 2.5.4, sklearn 1.9.1,
  pandas 3.1.1. **`datasets` pinned to 3.6.0** after 4.0.0/5.x return a `Column` for
  `ds[split]["text"]` and break `prepare_data.py` for mlab_imdb; with 3.6.0 the setup succeeds. Current
  `uv pip freeze` sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (record in each
  node result; the earlier ar run used the pre-pin 77-line freeze `dea8a9df…`). JAX env exists from
  `requirements_gpu.txt`.
- Static tests per suite were run CPU-masked (ar: 25 passed; mlab/mlgym: 18/22 passed, 3/4 deselected).

## Data (outside the repo, `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data`)

| Node | data_manifest sha256 | size |
|---|---|---|
| autoresearch_fixedtokens | `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51` | 963 M |
| mlab_cifar10 | `43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3` | 517 M |
| mlab_imdb | `a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c` | 379 M |
| mlab_ogbn_arxiv | `9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c` | 286 M |
| mlgym_cifar10 | `c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40` | 177 M |
| mlgym_fmnist | `8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c` | 53 M |

- `mlgym_breakout_minatar` has no data setup (`setup_command` empty); its U2 needs the JAX env.
- `mlgym_houseprice` remains **pending**: `R1-TRACKG-PORT-DECISIONS` (2) requires the user's Kaggle
  `train.csv` via `--from-file` (not MLGym's copy); no Kaggle credentials/data are present. That node is a
  per-node STOP pending the author, unless a Kaggle file is supplied.

## Next

Each remaining node runs under its own reviewed per-node U2 unit (same procedure as
`TRACKG_U2_AR_RESULT_20261117.md`, with the node's own `port_smoke_gpu` table, budget and env; House Prices
CPU-only). No GPU job is started by this prep record; no evidence/noise/D21/D28 on Ada.
