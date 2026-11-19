# Script sources for this node's U2 capture (mlgym_breakout_minatar, JAX)

- `run_node_jax.sh`, `verify_u2_records_jax.py`, `compute_sampler_max.py`: the Ada campaign scripts in their
  post-run state, copied byte-identically from `/home/dowling/r1_engineering/u2_iso_20261119/scripts/`.
  sha256: `run_node_jax.sh` **`4b5113fe310ac2438b59889d7d71cc2a910ec7d8a1b31e842115d8295a9a1997`**,
  `verify_u2_records_jax.py` **`8822495f0007de346a6e1aa505003de6b112b8022bf681e01cea933bcbd4e100`**,
  `compute_sampler_max.py` **`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`** (the copies
  here have the same shas; re-verified live read-only).

- **Verifier v1 → fixed — claim correction (result-review condition S2).** Unlike the five torch-node results,
  this campaign preserved **no separate verifier patch file** and **no copy of the v1 verifier source**. The live
  `verify_u2_records_jax.py` was edited in place (mtime `2026-11-18 21:06` local on Ada), and only the **v1
  outputs** are preserved in the result directory:
  `../verify_full.v1_verifier_bug.json` sha256
  `75a9fc92c2a5d4e4354366521a130d655d9851f5e57e824a3ca4c4aaa449f467` and
  `../verify_full.summary.v1_verifier_bug.txt` sha256
  `c027c74b69a654d622e545773b963ad2dafe3f387e8439b19c338032fe7f9e7b`. The v1 check names in those outputs are
  the only preserved description of the v1 rules: it required every `determinism.not_forced` reason to be
  `torch_absent` (it rejected the `dataloader_workers` "advertised via AR_NUM_WORKERS only" reason on every
  executed record) and it required `returncode 0` for the deliberately divergent `s002` (which exits 4). The
  fixed verifier checks rc 0 only for ok runs and accepts the JAX-specific determinism reasons; it was re-run on
  the same records (`verify_full.json` `ok: true`, 9 records / 8 executed / refused `s001`), with no smoke re-run.

- **Residual (recorded, not guessed).** The v1 verifier source and its fix diff/patch cannot be reconstructed
  byte-exactly without guessing, so none is provided here. The fixed verifier's own docstring (lines 10–12)
  still describes the v1 rule — cosmetic, not used by any check. The earlier result wording that `scripts/`
  contained "the documented fix patches" was inaccurate and is corrected in the result.

- The runner/verifier history for this node is otherwise the same campaign-level one as the five-node results
  (the `_patch*.py` files there are the torch-node launcher/verifier patches, not this JAX verifier's fix).
